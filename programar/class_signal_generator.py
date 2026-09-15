#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Clase para controlar el generador de funciones/arbitrario Picotest G5100A
# via VISA (SCPI). Mismo patron que class_spectrum_analyzer.py: se abre una
# conexion VISA (Ethernet/USB/GPIB) usando una cadena tipo
# 'TCPIP0::<ip>::inst0::INSTR' (o 'USB0::...::INSTR', 'GPIB0::<addr>::INSTR')
# y se le mandan comandos SCPI. Los comandos del G5100A son compatibles con
# la sintaxis SCPI estandar tipo Agilent/Keysight (FUNC, FREQ, VOLT, OUTP...).

import pyvisa

class signal_generator:
    def __init__(self, instrument_info, dummy_connect = False, **kwargs):
        # instrument_info: string de conexion VISA del equipo (IP/puerto,
        # USB o GPIB).
        # dummy_connect=True: no se conecta a ningun instrumento real. Sirve
        # para poder usar la clase (por ejemplo probar codigo) sin tener el
        # generador enchufado.
        self.dummy_connect = dummy_connect

        if self.dummy_connect == False:
            # Abre la conexion VISA con el instrumento.
            self.rm = pyvisa.ResourceManager()
            self.rm.list_resources()
            self.instrument = self.rm.open_resource(instrument_info)
            # *IDN? le pregunta al equipo quien es (fabricante, modelo, etc).
            # Se chequea que el modelo sea el G5100A esperado, para evitar
            # mandarle estos comandos a otro instrumento conectado por error.
            self.device_info = self.instrument.query('*IDN?')
            if self.device_info.split(',')[1].strip() != 'G5100A':
                self.instrument.close()
                raise ValueError(
                    f"Error: this is not the Picotest G5100A. "
                    f"*IDN? respondio: {self.device_info!r}"
                )
            print("Object binded to Picotest G5100A Waveform Generator")
            self.device_opened = True
            self.function = None
            # current_configuration: ultima configuracion leida/aplicada en
            # el equipo. new_configuration: valores que se van escribiendo
            # en el equipo en set_device_configuration.
            self.current_configuration = {}
            self.new_configuration = {}
        else:
            print("Object created in dummy mode.")

    def set_waveform(self, function, **kwargs):
        # Selecciona la forma de onda de salida (funcion) y de paso
        # configura frecuencia/amplitud/offset/etc si se pasan como
        # argumentos (ver set_device_configuration).
        valid_functions = {
            "sine": "SIN",
            "square": "SQU",
            "ramp": "RAMP",
            "pulse": "PULS",
            "noise": "NOIS",
            "dc": "DC",
        }
        if function not in valid_functions:
            raise ValueError(f"Unsupported waveform - {function}. Check the valid ones:"
                              f"\n{list(valid_functions.keys())}")

        self.instrument.write(f"FUNC {valid_functions[function]}")
        self.function = function
        print(f"G5100A output function set to {function}")

        if kwargs:
            self.set_device_configuration(**kwargs)

    def get_device_mode(self):
        # Le pregunta al equipo (via SCPI) que funcion tiene seleccionada
        # actualmente.
        return self.instrument.query("FUNC?").strip()

    def set_device_configuration(self, **kwargs):
        # Escribe en el equipo (via SCPI) los parametros que se le pasen
        # como argumentos con nombre, por ejemplo:
        #   set_device_configuration(frequency=1e6, amplitude=0.5, offset=0)
        # Solo se escriben los parametros que se pasaron explicitamente; el
        # resto queda como estaba en el equipo.
        # frequency: Hz | amplitude: en la unidad configurada (Vpp por
        # defecto) | offset: V (dc offset) | duty_cycle: % (solo onda
        # cuadrada) | load: ohms o "INF" (alta impedancia) | unit: "VPP",
        # "VRMS" o "DBM".
        for key, value in kwargs.items():
            if value is not None:
                self.new_configuration[key] = value

        if "frequency" in self.new_configuration:
            self.instrument.write(f"FREQ {self.new_configuration['frequency']}")
        if "amplitude" in self.new_configuration:
            self.instrument.write(f"VOLT {self.new_configuration['amplitude']}")
        if "offset" in self.new_configuration:
            self.instrument.write(f"VOLT:OFFS {self.new_configuration['offset']}")
        if "duty_cycle" in self.new_configuration:
            self.instrument.write(f"FUNC:SQU:DCYC {self.new_configuration['duty_cycle']}")
        if "load" in self.new_configuration:
            self.instrument.write(f"OUTP:LOAD {self.new_configuration['load']}")
        if "unit" in self.new_configuration:
            self.instrument.write(f"VOLT:UNIT {self.new_configuration['unit']}")

        self.current_configuration.update(self.new_configuration)

    def get_device_configuration(self):
        # Le pregunta al equipo (via SCPI) la configuracion de salida
        # actual y la guarda en self.current_configuration.
        current_configuration = {
            "function": self.instrument.query("FUNC?").strip(),
            "frequency": float(self.instrument.query("FREQ?")),
            "amplitude": float(self.instrument.query("VOLT?")),
            "offset": float(self.instrument.query("VOLT:OFFS?")),
            "unit": self.instrument.query("VOLT:UNIT?").strip(),
            "load": self.instrument.query("OUTP:LOAD?").strip(),
        }
        self.current_configuration = current_configuration
        return current_configuration

    def output_on(self):
        # Habilita la salida (conector Output del panel frontal).
        self.instrument.write("OUTP ON")

    def output_off(self):
        # Deshabilita la salida.
        self.instrument.write("OUTP OFF")

    def get_output_state(self):
        # Devuelve True si la salida esta habilitada, False si no.
        return bool(int(self.instrument.query("OUTP?")))

    def get_timeout(self):
        # Timeout de comunicacion VISA (en ms).
        return self.instrument.timeout

    def set_timeout(self, new_timeout):
        self.instrument.timeout = new_timeout

    def close_device(self):
        # Apaga la salida (por seguridad, para no dejar una señal activa
        # conectada al circuito) y cierra la conexion VISA. Seguro llamarla
        # mas de una vez.
        if self.device_opened == True:
            self.output_off()
            self.instrument.close()
            self.device_opened = False
