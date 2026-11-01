from pathlib import Path
import numpy as np
import tarfile
import io
import logging
from scipy.io import savemat
import pandas as pd
import os

PAGE_SIZE = 512
CHANNELS = [32, 3, 3, 6, 3]
MEASUREMENTS_PER_PAGE = 252 // sum(CHANNELS)
MEASUREMENT_SIZE = sum(CHANNELS) * 2    # 94 байта

HEADER_SIZE = 512
CALIBRATION_VALUES = 24 + 6 + 9    # 39 int16
DEVICE_INFO_SIZE = 1024 - CALIBRATION_VALUES * 2

def decode_text(data):
    data = data.rstrip(b"\x00")

    for encoding in ("utf-8", "cp1251", "cp866"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass

    return data.decode("latin1", errors="replace")


def read_dollar_fields(data):
    text = decode_text(data)

    return [
        field.replace("\x00", "").strip()
        for field in text.split("$")
    ]

def get_field(fields, index):
    if index < len(fields):
        return fields[index]
    return ""


class Project:
    def __init__(self):
        self.DATAS = {
                "b" : {},
                "a" : {},
                "w" : {},
                "t" : {},
                "c" : {}}
        self.filename = None
        self.edited = False
        
    def getByKey(self, key : str):
        y_key = None
        if "|" in key:
            y_key = key.split("|")[-1]
            try:
                y_key = int(y_key)
            except:
                y_key = None
            else:
                key = "|".join(key.split("|")[:-1])
        keys = key.split("\\")
        if len(keys) > 2:
            logging.warning(f"|PROJECT|getByKey|\tПуть ключа данных больше чем ожидалось! {keys=}")
            raise SystemError("Путь ключа данных больше чем ожидалось!")
        elif len(keys) == 2:
            logging.info(f"|PROJECT|getByKey|\t2 ключа {keys=}")
            return self.DATAS[keys[0]][keys[1]] if y_key is None else self.DATAS[keys[0]][keys[1]][y_key]
        elif len(keys) == 1:
            logging.info(f"|PROJECT|getByKey|\t1 ключ {keys=}")
            return self.DATAS[keys[0]] if y_key is None else self.DATAS[keys[0]][y_key]
        else:
            logging.warning(f"|PROJECT|getByKey|\tПуть ключа данных меньше чем ожидалось! {keys=}")
            raise SystemError("Путь ключа данных меньше чем ожидалось!")
        
    def loadFromSphere(self, filename):
        path = Path(filename)
        logging.info(f"|PROJECT|loadFromSphere|\tЗагрузка: {filename}")
        
        if not path.is_file():
            logging.warning(f"|PROJECT|loadFromSphere|\tФайл не найден: {path.is_file()=}")
            print("Такого файла не существует!")
            return None
    
        if path.stat().st_size < 2048:
            logging.warning(f"|PROJECT|loadFromSphere|\tФайл слишком маленький: {path.stat().st_size=} < 2048")
            print("Файл слишком маленький.")
            return None
    
        raw = path.read_bytes()

        # Информация в начале файла, первые 512 байт

        file_header = raw[:HEADER_SIZE]
        start_fields = read_dollar_fields(file_header)
    
        start_info = {
            "object_name": get_field(start_fields, 1),
            "date": get_field(start_fields, 2),
            "time": get_field(start_fields, 3),
        }
        logging.info(f"|PROJECT|loadFromSphere|\tИнформация из начала файла: {start_info=}")
    
        # Маркеры начала и конца страницы
        marker_1 = file_header[-1]
        marker_2 = file_header[1]
        marker_3 = file_header[2]
        marker_4 = file_header[3]
    
        offset = HEADER_SIZE

        # Калибровка, 39 значений int16 big-endian

        calibration_bytes = CALIBRATION_VALUES * 2
    
        calibration_raw = np.frombuffer(
            raw,
            dtype=">i2",
            count=CALIBRATION_VALUES,
            offset=offset,
        ).astype(np.float64)
    
        offset += calibration_bytes
    
        calibration_a = np.zeros(9, dtype=np.float64)
    
        calibration_a[0:3] = calibration_raw[-12:-9]
        calibration_a[[3, 5, 8]] = calibration_raw[-9:-6] / 10000.0 + 1.0
        calibration_a[[4, 6, 7]] = calibration_raw[-6:-3] / 10000.0

        # Информация о приборе

        device_block = raw[offset:offset + DEVICE_INFO_SIZE]
        offset += DEVICE_INFO_SIZE
    
        device_fields = read_dollar_fields(device_block)
    
        device_name = get_field(device_fields, 1)
        device_number = get_field(device_fields, 2)
    
        device_info = {
            "name": device_name,
            "number": device_number,
            "number_prefix": device_number[:6],
            "number_suffix": device_number[6:],
        }
        logging.info(f"|PROJECT|loadFromSphere|\tИнформация о девайсе: {device_info=}")
    
        # Основные данные и конечный информационный блок
    
        payload = raw[offset:]
    
        if len(payload) < PAGE_SIZE:
            logging.warning(f"|PROJECT|loadFromSphere|\tВ файле отсутствуют страницы измерений. {len(payload)=} < {PAGE_SIZE=}")
            return None
    
        # Последние 512 байт являются информационным блоком
        
        footer = payload[-PAGE_SIZE:]
        pages_data = payload[:-PAGE_SIZE]
    
        end_fields = read_dollar_fields(footer)
    
        end_info = {
            "object_name": get_field(end_fields, 1),
            "date": get_field(end_fields, 2),
            "time": get_field(end_fields, 3),
        }
        logging.info(f"|PROJECT|loadFromSphere|\tИнформация из конца файла: {end_info=}")
    
        page_count = len(pages_data) // PAGE_SIZE
    
        measurements = []
        page_counters = []
    
        for page_index in range(page_count):
            page_start = page_index * PAGE_SIZE
            page = pages_data[page_start:page_start + PAGE_SIZE]
    
            if len(page) != PAGE_SIZE:
                break
    
            valid = (
                page[0] == marker_1
                and page[1] == marker_2
                and page[510] == marker_3
                and page[511] == marker_4
            )
    
            if not valid:
                logging.warning(f"|PROJECT|loadFromSphere|\tПовреждённая страница: {page_index=} (Сообщение будет проигнорированно)")
    
            # На каждой странице находится 5 измерительных актов
            
            for measurement_index in range(MEASUREMENTS_PER_PAGE):
                begin = 2 + measurement_index * MEASUREMENT_SIZE
                end = begin + MEASUREMENT_SIZE
    
                values = np.frombuffer(
                    page[begin:end],
                    dtype="<i2",       # little-endian int16
                    count=sum(CHANNELS),
                )
    
                measurements.append(values)
    
            counter = np.frombuffer(
                page[506:510],
                dtype="<u4",
                count=1,
            )[0]
    
            page_counters.append(counter)
    
        if measurements:
            matrix = np.stack(measurements, axis=1).astype(np.float64)
        else:
            matrix = np.empty((sum(CHANNELS), 0), dtype=np.float64)
    
        ret = {"b" : (matrix[0:CHANNELS[0]] - 2**15) * 4e-4,
                "a" : matrix[CHANNELS[0]:sum(CHANNELS[:2])],
                "w" : matrix[sum(CHANNELS[:2]):sum(CHANNELS[:3])],
                "t" : matrix[sum(CHANNELS[:3]):sum(CHANNELS[:4])],
                "c" : matrix[sum(CHANNELS[:4]):sum(CHANNELS[:5])]}
        
        for key in self.DATAS.keys():
            if "sphere" not in self.DATAS[key].keys():
                self.DATAS[key]["sphere"] = ret[key]
            else:
                self.DATAS[key]["sphere"] = np.hstack((self.DATAS[key]["sphere"], ret[key]))
                    
        self.edited = True
        
        logging.info(f"|PROJECT|loadFromSphere|\tЗагрузка: {filename=} завершена!")

    def NewProject(self):
        self.DATAS = {
            "b" : {},
            "a" : {},
            "w" : {},
            "t" : {},
            "c" : {}}
        self.filename = None
    
    def SaveProject(self, filename : None|str = None):
        logging.info(f"|PROJECT|SaveProject|\tСохранение: {filename=}")
        if filename is None:
            filename = self.filename
            logging.info(f"|PROJECT|SaveProject|\t{filename=}")
        if filename is None:
            logging.warning(f"|PROJECT|SaveProject|\tФайл всё ещё None {filename=}\t\t=>\t\tКуда ставить то? КУДА СТАВИТЬ!?")
            raise SystemError("Куда ставить то? КУДА СТАВИТЬ!?")
        
        if filename.endswith(".tar.zst") == True:
            self.filename = filename[:-8]
        else:
            self.filename = filename
            
        logging.info(f"|PROJECT|SaveProject|\tЗапись в: {self.filename+".tar.zst"}")
        with tarfile.open(name=self.filename+".tar.zst", mode='w:zst') as archive:
            for key in self.DATAS.keys():
                for sub_key in self.DATAS[key].keys():
                    info = tarfile.TarInfo(name=f"{key}_{sub_key}.npy")
                    buffer = io.BytesIO()
                    
                    np.save(buffer, self.DATAS[key][sub_key])
                    info.size = buffer.getbuffer().nbytes
                    buffer.seek(0)
                    
                    archive.addfile(info, buffer)
        
        self.edited = False
        
    def LoadProject(self, filename : str):
        logging.info(f"|PROJECT|LoadProject|\tЗагрузка: {filename=}")
        self.NewProject()
        self.filename = filename
        if self.filename.endswith(".tar.zst") == True:
            self.filename = self.filename[:-8]
        
        logging.info(f"|PROJECT|LoadProject|\tЧтение из: {self.filename+".tar.zst"}")
        with tarfile.open(name=self.filename+".tar.zst", mode='r:zst') as archive:
            for files in archive.getnames():
                keys = files.split(".")[0].split("_")
                if len(keys) == 1:
                    with archive.extractfile(f"{keys[0]}.npy") as file:
                        self.DATAS[keys[0]] = np.load(io.BytesIO(file.read()))
                elif len(keys) == 2:
                    with archive.extractfile(f"{keys[0]}_{keys[1]}.npy") as file:
                        self.DATAS[keys[0]][keys[1]] = np.load(io.BytesIO(file.read()))

    def SaveMat(self, filename : None|str = None, key : None|str = None):
        logging.info(f"|PROJECT|SaveMat|\tСохранение: {filename=}")
        if filename is None:
            filename = self.filename
            logging.info(f"|PROJECT|SaveMat|\t{filename=}")
        if filename is None:
            logging.warning(f"|PROJECT|SaveMat|\tФайл всё ещё None {filename=}\t\t=>\t\tКуда ставить то? КУДА СТАВИТЬ!?")
            raise SystemError("Куда ставить то? КУДА СТАВИТЬ!?")
        
        dataForSaving = {}
        for key in self.DATAS.keys():
            if len(self.DATAS[key].keys()) == 0:
                logging.warning(f"|PROJECT|SaveMat|\tНе достаточно данных для экспорта! Нет данных {key}")
                raise SystemError(f"Не достаточно данных для экспорта!\nНет данных {key}")
            for sub_key in self.DATAS[key].keys():
                if key in dataForSaving.keys():
                    dataForSaving[key][sub_key] = self.DATAS[key][sub_key]
                else:
                    dataForSaving[key] = {sub_key : self.DATAS[key][sub_key]}
            
        if filename.endswith(".mat") == False:
            filename = f"{filename}.mat"
        logging.info(f"|PROJECT|SaveMat|\tЗапись в: {filename}")
        savemat(filename, dataForSaving, do_compression=True)
    
    def SaveCsv(self, path : str, key : None|str  = None):
        for key in self.DATAS.keys():
            for sub_key in self.DATAS[key].keys():
                tPath = os.path.join(path, f"{key}_{sub_key}.csv")
                logging.info(f"|PROJECT|SaveCsv|\tЗапись CSV в: {tPath}")
                np.savetxt(tPath, self.DATAS[key][sub_key])

    def SaveXlsx(self, filename : str, key : None|str  = None):
        if filename.endswith(".xlsx") == False:
            filename = f"{filename}.xlsx"
            
        logging.info(f"|PROJECT|SaveXlsx|\tЗапись в: {filename}")
        with pd.ExcelWriter(filename) as writer:
            for key in self.DATAS.keys():
                for sub_key in self.DATAS[key].keys():
                    pd.DataFrame(self.DATAS[key][sub_key]).to_excel(
                        writer,
                        sheet_name=f"{key}_{sub_key}",
                        index=False,
                        header=False,
                    )
    
    def __str__(self):
        return str(self.filename) + " " + str(self.DATAS)
    
if __name__ == "__main__":
    ts = Project()
    ts.loadFromSphere("2_1.sgm")
    print(ts)
    ts.SaveProject("output")
    ts.LoadProject("output")
    print(ts)