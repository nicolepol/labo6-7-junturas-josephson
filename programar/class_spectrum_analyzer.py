#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Clase para controlar el analizador de espectro / de señales Keysight N9021B
# vía VISA (SCPI), y para guardar/leer las mediciones en archivos csv.
#
# La comunicación con el instrumento se hace con pyvisa: se abre una conexión
# ("resource") por Ethernet/GPIB/USB usando una cadena tipo
# 'TCPIP0::<ip>::inst0::INSTR', y a partir de ahí se le mandan comandos SCPI
# (strings como ":SENS:FREQ:STAR?") que el equipo entiende. "?" al final del
# comando es una consulta (el equipo responde un valor); sin "?" es una orden
# (el equipo ejecuta algo, no responde nada por si solo).

import pyvisa
import numpy as np
import time
import csv
import pandas as pd

class spectrum_analyzer:
    def __init__(self, instrument_info, dummy_connect = False, **kwargs):
        # instrument_info: string de conexion VISA del equipo (IP/puerto).
        # dummy_connect=True: no se conecta a ningun instrumento real. Sirve
        # para poder usar la clase solo para leer/procesar datos ya guardados
        # (por ejemplo con read_data) sin tener el equipo enchufado.
        # storage_path: carpeta donde se guardan/leen los csv de datos.
        # force_stay_open: si es True, no se cierra la conexion automaticamente
        # despues de cada adquisicion (util para hacer varias mediciones
        # seguidas sin reabrir la conexion cada vez).
        self.storage_path = kwargs.get('storage_path')
        self.force_stay_open = kwargs.get('force_stay_open', False)
        self.dummy_connect = dummy_connect

        if self.dummy_connect == False:
            # Abre la conexion VISA con el instrumento.
            self.rm = pyvisa.ResourceManager()
            self.rm.list_resources()
            self.instrument = self.rm.open_resource(instrument_info)
            # *IDN? le pregunta al equipo quien es (fabricante, modelo, etc).
            # Se chequea que el modelo sea el N9021B esperado, para evitar
            # mandarle comandos de este analizador a otro instrumento distinto
            # conectado por error.
            self.device_info = self.instrument.query('*IDN?')
            if self.device_info.split(',')[1].strip() != 'N9021B':
                self.instrument.close()
                raise ValueError(
                    f"Error: this is not the Keysight SA N9021B. "
                    f"*IDN? respondio: {self.device_info!r}"
                )
            print("Object binded to Keysight N9021B Signal Analyzer")
            self.device_opened = True
            self.mode_defined = False
            # current_configuration: ultima configuracion leida/aplicada en el
            # equipo (frecuencias, RBW, VBW, etc). new_configuration: valores
            # que se van a escribir en el equipo en set_device_configuration.
            self.current_configuration = {}
            self.new_configuration = {}
        else:
            print("Object created in dummy mode. It is useful for data processing.")

    def set_mode(self, mode):
        # Define en que modo de medicion va a trabajar el equipo. Por ahora
        # solo "SA" (Spectrum Analyzer, barrido de frecuencias) esta
        # completamente implementado en el resto de la clase; los demas
        # modos ("IQ", "PN", "RT") estan como placeholders para el futuro.
        # Checking mode
        if mode == "SA":
            print('Spectrum Analyzer Class configured in Spectrum Analyzer mode')  
            # self.instrument.write(':INST:SEL SA')            
        elif mode == "IQ":
            print('Spectrum Analyzer Class configured in IQ Anaylzer (Basic) mode')            
        elif mode == "PN":
            print('Spectrum Analyzer Class configured in Phase Noise mode')
        elif mode == "RT":
            print('Spectrum Analyzer Class configured in Real-Time Spectrum Analyzer mode')    
        elif mode == "data_analysis":
            print('Spectrum Analyzer Class configured in Data Analysis mode')
        else:
            raise ValueError(f"Unsupported operation mode - {mode}. Check the valid ones:"
                             "\nSA - Spectrum Analyzer\nIQ - IQ Analyzer (Basic)"
                             "\nPH - Phase noise\nRT - Real-Time Spectrum Analyzer"
                             "data_analysis - for doing data analysis with a set of tools.")
        
        self.mode = mode
        self.mode_defined = True
        # if operation == 'process': 
        #     print('Spectrum Analyzer Class - Process mode')
        #     if self.force_stay_open == False:
        #         self.device_opened = False

        # if operation == 'configure':
        #     print('Spectrum Analyzer Class - Configure mode')
        #     f_start = kwargs.get('f_start')
        #     f_stop = kwargs.get('f_stop')
        #     rbw = kwargs.get('rbw')
        #     vbw = kwargs.get('vbw')
        #     self.config_device(f_start, f_stop, rbw, vbw)
        #     self.close_device()

    def get_device_mode(self):
        # Devuelve el modo actual (el que se fijo con set_mode). Tira error
        # si todavia no se llamo a set_mode al menos una vez.
        if self.mode_defined == False:
            raise ValueError(f"The devices hasn't being configured.")
        else:
            return self.mode

    def get_device_configuration(self):
        # Le pregunta al equipo (via SCPI) los parametros de barrido que
        # tiene configurados actualmente y los guarda en
        # self.current_configuration. Util para saber "que hay puesto en el
        # equipo ahora" sin haberlo fijado nosotros mismos (por ejemplo si
        # alguien lo configuro a mano desde el panel).
        if self.mode == "SA":
            print('Spectrum Analyzer Class configured in Spectrum Analyzer mode')
            print('Retrieving device configuration ...')
            # f_start/f_stop: extremos del barrido en frecuencia [Hz].
            f_start = float(self.instrument.query(":SENS:FREQ:STAR?"))
            f_stop  = float(self.instrument.query(":SENS:FREQ:STOP?"))
            f_center = float(self.instrument.query(":SENS:FREQ:CENT?"))  # frecuencia central [Hz]
            span = float(self.instrument.query(":SENS:FREQ:SPAN?"))  # ancho de la ventana en frecuencia [Hz]
            rbw = float(self.instrument.query(":SENS:BAND:RES?"))  # Resolution BandWidth [Hz]: resolucion espectral del barrido
            vbw = float(self.instrument.query(":SENS:BAND:VID?"))  # Video BandWidth [Hz]: filtro de suavizado sobre la traza
            n_points = int(self.instrument.query(":SWE:POIN?"))  # cantidad de puntos del barrido (largo del vector de frecuencias)

            current_configuration = {
                "f_start": f_start,
                "f_stop": f_stop,
                "f_center": f_center,
                "span": span,
                "rbw": rbw,
                "vbw": vbw,
                "n_points": n_points,
            }

            self.current_configuration = current_configuration
            
        elif self.mode == "IQ":
            pass
        elif self.mode == "PN":
            pass
        elif self.mode == "RT":
            pass
        else:
            raise ValueError(f"An invalide mode was configured.")

        return current_configuration
            
    def set_device_configuration(self, **kwargs):
        # Escribe en el equipo (via SCPI) los parametros de barrido que se le
        # pasen como argumentos con nombre, por ejemplo:
        #   set_device_configuration(f_start=10e6, f_stop=50e6, rbw=10e3)
        # Solo se escriben los parametros que se pasaron explicitamente
        # (los que quedan en None por no haber sido pasados no se tocan), asi
        # que se puede cambiar un solo parametro sin pisar el resto de la
        # configuracion ya cargada en el equipo.
        # self.mode = kwargs.get('mode')
        # SA mode
        f_start = kwargs.get('f_start')
        f_stop = kwargs.get('f_stop')
        f_center = kwargs.get('f_center')
        span = kwargs.get('span')
        rbw = kwargs.get('rbw')
        vbw = kwargs.get('vbw')
        n_points = kwargs.get('n_points', 1001)           
        ref_lvl = kwargs.get('ref_lvl', 0)   
        # IQ Mode
        # center_freq = kwargs.get('center_freq')        
        # digital_if = kwargs.get('digital_if')        
        # measurement_time = kwargs.get('measurement_time')        
        # attenuator = kwargs.get('attenuator')        

        if self.mode == "SA":
            # Actualiza self.new_configuration solo con los parametros que
            # efectivamente se pasaron (descarta los None), y va acumulando
            # sobre lo que ya habia (por eso no se reinicia el diccionario
            # entero en cada llamada).
            for key, value in kwargs.items():
                if value != None:
                    self.new_configuration[key] = value
                # self.new_configuration[key] = value

            # self.new_configuration = {
            #                 "f_start": f_start,
            #                 "f_stop": f_stop,
            #                 "f_center": f_center,
            #                 "span": span,
            #                 "rbw": rbw,
            #                 "vbw": vbw,
            #                 "n_points": n_points,
            #             }
            print(self.new_configuration)

            # Por cada parametro presente en new_configuration se manda el
            # comando SCPI correspondiente al equipo para efectivamente
            # cambiar esa configuracion.
            if "f_start" in self.new_configuration:
                self.instrument.write(f":SENS:FREQ:STAR {self.new_configuration["f_start"]}")
            if "f_stop" in self.new_configuration:
                self.instrument.write(f":SENS:FREQ:STOP {self.new_configuration["f_stop"]}")
            if "f_center" in self.new_configuration:
                self.instrument.write(f":SENS:FREQ:CENT {self.new_configuration["f_center"]}")
            if "span" in self.new_configuration:
                self.instrument.write(f":SENS:FREQ:SPAN {self.new_configuration["span"]}")
            if "rbw" in self.new_configuration:
                self.instrument.write(f":SENS:BAND:RES {self.new_configuration["rbw"]}")
            if "vbw" in self.new_configuration:
                self.instrument.write(f":SENS:BAND:VID {self.new_configuration["vbw"]}")                        
            if "n_points" in self.new_configuration:
                self.instrument.write(f":SWE:POIN {self.new_configuration["n_points"]}")
                # self.instrument.write(f':SENS:SWE:POIN {n_points}')

            # self.instrument.write(f':SENS:POW:ATT AUTO')      # Set input signal attenuator
            # self.instrument.write(f'DISP:WIND:TRAC:Y:RLEV {ref_lvl} dBm')

            # instrument.write(":FORMat:BORDer SWAPed")  # Set byte order for binary data
            # instrument.write(":FORMat:DATA REAL,32")  # Set data format to 32-bit floating point
            # self.instrument.write(":FORMat:DATA ASC")  # Set data format to ASCii    
            # El sweep time (tiempo de barrido) lo calcula el equipo solo, en
            # funcion de span/RBW/VBW/n_points recien configurados; se lo
            # vuelve a pedir aca solo para mostrarlo en pantalla.
            sweep_time = float(self.instrument.query('SENS:SWE:TIME?'))
            print(f'Current Sweep Time: {sweep_time*1000} ms | {sweep_time} seconds | {sweep_time/60} minutes')

            # Update current_configuration
            self.current_configuration = self.new_configuration

            # if self.force_stay_open == False:
            #     self.close_device()

        # if self.mode == "IQ": # Select IQ Analyzer mode
        #     self.instrument.write(':INST:SEL BASIC')
        #     self.instrument.write(':CONF:WAV')      # Set IQ waveform measurement
        #     self.instrument.write(':DISP:WAV:VIEW IQ')      # Display I/Q waveforms
        #     self.instrument.write(':INIT:CONT OFF')      # Disables continuous sweep
        #     self.instrument.write(f':FREQ:CENT {center_freq}')      # Set center frequency (IQ LO?)
        #     self.instrument.write(f':WAV:DIF:BAND {digital_if}')      # Set Digital IF (Information BW)
        #     self.instrument.write(f':SENS:WAV:SWE:TIME {measurement_time}')      # Set measurement time to max
        #     self.instrument.write(f':SENS:POW:ATT {attenuator}')      # Set input signal attenuator
        #     self.instrument.write(':SENS:WAV:IF:GAIN LOW')      # Set IF gain range (AUTO / LOW (default) / HIGH)

    def get_sweep_time(self):
        # Tiempo que tarda el equipo en completar un barrido, en segundos.
        return float(self.instrument.query('SENS:SWE:TIME?'))

    def marker_peak_search(self, marker = 1):
        # Prende el marcador indicado y le hace un "peak search": lo mueve
        # al punto de mayor amplitud de la traza que esta ahora en pantalla
        # (equivalente a apretar Peak Search en el panel frontal). Como el
        # marcador se ve en la pantalla fisica del equipo, sirve para
        # confirmar a ojo que realmente esta enganchado al pico de la señal
        # y no a un punto cualquiera cercano. Devuelve (frecuencia, amplitud)
        # del marcador: frecuencia en Hz, amplitud en dBm.
        self.instrument.write(f":CALC:MARK{marker}:STATE ON")
        self.instrument.write(f":CALC:MARK{marker}:MAX")
        marker_freq = float(self.instrument.query(f":CALC:MARK{marker}:X?"))
        marker_amplitude = float(self.instrument.query(f":CALC:MARK{marker}:Y?"))
        return marker_freq, marker_amplitude

    def get_timeout(self):
        # Timeout de comunicacion VISA (en ms): cuanto espera pyvisa una
        # respuesta del equipo antes de tirar un error de timeout.
        return self.instrument.timeout

    def set_timeout(self, new_timeout):
        self.instrument.timeout = new_timeout
        # print(f"New timeout: {new_timeout}")

    def stop_continuous_mode(self):
        # Pone al equipo en modo "single sweep": hace un barrido cuando se le
        # pide (:INIT:IMM) y despues se queda quieto, en vez de barrer todo
        # el tiempo. Es necesario para poder controlar bien cuando empieza y
        # termina cada adquisicion.
        self.instrument.write(":INIT:CONT OFF")

    def start_continuous_mode(self):
        # Vuelve al modo de barrido continuo (el normal cuando se usa el
        # equipo a mano desde el panel).
        self.instrument.write(":INIT:CONT ON")

    def _wait_acq_to_complete(self, avg = 1, margin = 2.0):
        # Espera a que el equipo termine el barrido (o los "avg" barridos, si
        # se promedia) antes de seguir. Se hace subiendo temporalmente el
        # timeout de VISA a algo mayor que el tiempo de barrido esperado
        # (sweep*avg + margen de seguridad en segundos, pasado a ms), y
        # despues usando *OPC? ("Operation Complete?"), que es un comando
        # SCPI que no responde hasta que el equipo termino lo que estaba
        # haciendo. El timeout original se restaura siempre al final (por
        # eso el try/finally), incluso si algo falla en el medio.
        sweep = self.get_sweep_time()
        old_timeout = self.get_timeout()

        try:
            self.set_timeout(int((sweep + margin) * avg * 1000))
            self.instrument.query("*OPC?")
        finally:
            self.set_timeout(old_timeout)

    def acquire(self, save_to_file = False, **kwargs):
        # Dispara una adquisicion en el equipo y devuelve los datos medidos.
        # En modo "SA" devuelve (frecuencia, amplitud); en modo "IQ" devuelve
        # (tiempo, I, Q). Si save_to_file=True, ademas guarda el resultado en
        # un csv (usando save_data) con el nombre pasado en file_name.
        # print('Doing acquisition with Spectrum Analyzer')

        if self.mode == "SA":
            n_avg = kwargs.get('n_avg', 1)
            # self.extend_acq_time_multiplier = kwargs.get('extend_acq_time_multiplier', 1)
            
            # start_freq_command = 'SENS:FREQ:STAR?'
            # stop_freq_command = 'SENS:FREQ:STOP?'
            # num_points_command = 'SENS:SWE:POIN?'
            # self.sweep_time = float(self.instrument.query('SENS:SWE:TIME?'))*self.extend_acq_time_multiplier

            # self.num_points = int(self.instrument.query(num_points_command))
            # start_freq = float(self.instrument.query(start_freq_command))
            # stop_freq = float(self.instrument.query(stop_freq_command))
            # self.get_device_configuration()

            # Calculate the frequency span and create a frequency array
            # El equipo devuelve solo la amplitud de cada punto del barrido
            # (el eje Y); el eje de frecuencias (eje X) hay que reconstruirlo
            # nosotros mismos como un arreglo equiespaciado entre f_start y
            # f_stop, con la cantidad de puntos configurada (n_points).
            self.frequency_span = self.current_configuration["f_stop"] - self.current_configuration["f_start"]
            self.frequency_array = np.linspace(self.current_configuration["f_start"],
                                               self.current_configuration["f_stop"],
                                               self.current_configuration["n_points"])

            # Trigger the spectrum analyzer to start a new sweep
            sweep_time = float(self.instrument.query('SENS:SWE:TIME?'))
            # print(f'Current Sweep Time: {sweep_time*1000} ms | {sweep_time} seconds | {sweep_time/60} minutes\nWaiting ...')
            # trigger_command = 'INIT:IMM'
            # inst.write(":INIT")
            self.instrument.write(":INIT:IMM")
            # Wait for the sweep time
            # time.sleep(self.sweep_time)
            # self.instrument.query("*OPC?")
            # Espera bloqueante hasta que el barrido termine (ver
            # _wait_acq_to_complete) antes de intentar leer la traza.
            self._wait_acq_to_complete(n_avg)

            # Read the trace
            # Pide al equipo los valores de amplitud de la traza 1 (los que
            # se ven en pantalla), como un arreglo de numeros en dBm.
            self.spectrum_signal = np.asarray(self.instrument.query_ascii_values(":TRACe:DATA? TRACe1"))

            if save_to_file == True:
                file_name = kwargs.get('file_name')
                if file_name == None:
                    print("Error while saving data to file: file_name is not defined")
                else:
                    self.save_data(file_name)
            
            # print('Acquistion done')

            if self.force_stay_open == False:
                self.close_device()

            return self.frequency_array, self.spectrum_signal

        if self.mode == "IQ":
            # Modo IQ Analyzer: en vez de una traza en frecuencia, se
            # adquieren las componentes I y Q de la señal en el tiempo
            # (representacion en banda base de la señal de RF).
            # Trigger the spectrum analyzer to start a new sweep
            trigger_command = 'INIT:IMM'
            self.instrument.write(trigger_command)
            time.sleep(2)
            self.sample_rate = self.instrument.query_ascii_values(':FETC:WAV1?')[0]
            self.sample_number = int(self.instrument.query_ascii_values(':FETC:WAV1?')[3])
            self.time_trace = np.linspace(0, self.sample_rate*self.sample_number, self.sample_number)

            trigger_command = 'INIT:IMM'
            self.instrument.write(trigger_command)
            time.sleep(2)
            IQ_traces = self.instrument.query_ascii_values(':FETC:WAV0?')
            print('Getting I/Q traces ...')

            # El equipo devuelve I y Q intercalados en un solo arreglo
            # (I0, Q0, I1, Q1, ...), por eso se separan tomando elementos de
            # a uno salteando el otro (slicing con paso 2).
            self.I_trace = np.asarray(IQ_traces[0::2])
            self.Q_trace = np.asarray(IQ_traces[1::2])

            if save_to_file == True:
                file_name = kwargs.get('file_name')
                if file_name == None:
                    print("Error while saving data to file: file_name is not defined")
                else:
                    self.save_data(file_name)

            print('Acquistion done')

            if self.force_stay_open == False:
                self.close_device()

            return self.time_trace, self.I_trace, self.Q_trace

    def save_data(self, file_name, dataformat="csv"):
        # Guarda en storage_path + file_name los ultimos datos adquiridos
        # (los que haya en self.frequency_array/spectrum_signal para modo SA,
        # o self.time_trace/I_trace/Q_trace para modo IQ). dataformat="csv"
        # escribe con el modulo csv estandar; "csv_pandas" arma un DataFrame
        # y usa pandas para escribir el archivo (mismo formato final, distinta
        # implementacion).
        if self.force_stay_open == False:
            self.close_device()
        print('Saving data to: ' + file_name)
        print('(Save path:' + self.storage_path +  ')')
        total_path = self.storage_path + file_name    

        if self.mode == "SA":
            if dataformat == "csv":
                with open(total_path, "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    csv_writer.writerow(["Frequency", "Amplitude"])  # Write header
                    for frequency, amplitude in zip(self.frequency_array, self.spectrum_signal):
                        csv_writer.writerow([frequency, amplitude]) 
            elif dataformat == "csv_pandas":
                df = pd.DataFrame({ "Frequency_Hz": self.frequency_array, "Amplitude_dBm": self.spectrum_signal})
                df.to_csv(total_path, index=False)
            else: 
                raise ValueError(f"Data format {dataformat} is unsupported. Select \"csv\" or \"csv_pandas\". Both are csv style, but differs in the how it is managed.")

        if self.mode == "IQ":
            if dataformat == "csv":
                with open(total_path, "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    csv_writer.writerow(["time_trace", "I_Trace", "Q_Trace"])  # Write header
                    for time_trace, I_trace, Q_trace in zip(self.time_trace, self.I_trace, self.Q_trace):
                        csv_writer.writerow([time_trace, I_trace, Q_trace])
            elif dataformat == "csv_pandas":
                df = pd.DataFrame({ "time_trace": self.time_trace, "I_Trace": self.I_trace, "Q_Trace": self.Q_trace})
                df.to_csv(total_path, index=False)
            else:
                raise ValueError(f"Data format {dataformat} is unsupported. Select \"csv\" or \"csv_pandas\". Both are csv style, but differs in the how it is managed.")
            
        print('Saving done')

    def read_data(self, file_name, **kwargs):
        # Lee un csv previamente guardado con save_data y devuelve los
        # arreglos de datos (frecuencia/amplitud para mode="SA", o
        # tiempo/I/Q para mode="IQ"). No necesita que el equipo este
        # conectado (funciona incluso en dummy_connect=True), ya que solo lee
        # un archivo del disco.
        mode = kwargs.get('mode')
        print_debug = kwargs.get('print_debug', True)

        if self.force_stay_open == False and self.dummy_connect == False:
            self.close_device()

        if print_debug:
            print('Reading data from: ' + file_name)
            print('(Source path:' + self.storage_path +  ')')
            
        total_path = self.storage_path + file_name  

        if mode == "SA":
            loaded_data = np.genfromtxt(total_path, delimiter=',', skip_header=1)
            freq_array = np.array(loaded_data[:, 0])
            amp_array = np.array(loaded_data[:, 1])
            
            return freq_array, amp_array

        if mode == "IQ":
            loaded_data = np.genfromtxt(total_path, delimiter=',', skip_header=1)
            time_array = np.array(loaded_data[:, 0])
            i_array = np.array(loaded_data[:, 1])
            q_array = np.array(loaded_data[:, 2])

            return time_array, i_array, q_array
    
    def close_device(self):
        # Deja el equipo en un estado "prolijo" antes de soltar la conexion:
        # lo vuelve al modo Spectrum Analyzer normal y a barrido continuo
        # (por si quedaba en single sweep), y despues cierra la conexion
        # VISA. Es seguro llamarla mas de una vez: si ya estaba cerrado
        # (device_opened == False) no hace nada.
        if self.device_opened == True:
            self.instrument.write(':SYSTem:PON:MODE SA')
            self.start_continuous_mode()
            self.instrument.close()
            self.device_opened = False
