from io import BytesIO
import logging
import re
from PIL import ImageDraw,ImageFont, Image

class Transporte:

    @staticmethod
    def __valida_patente(patente):
        if len(patente) == 0:
            return None

        patente = patente.replace("-", "")
        patente = patente.replace(" ", "")
        patente = patente.upper()

        if len(patente) != 6:
            logging.error(f"Longitud incorrecta para la patente > {patente}")
            return None
        
        paVieja=re.compile("[A-Z]{2}[\d]{4}") 
        paNueva=re.compile("[A-Z]{4}[\d]{2}") 

        if paVieja.search(patente) or paNueva.search(patente):
            return patente
        
        logging.error(f"[{patente}] > No es una patente Válida")
        return None

    @staticmethod
    def Read(patente):
        v_patente = Transporte.__valida_patente(patente)
        if v_patente is None:
            return None
        
        return v_patente

    @staticmethod
    def getImageCamion(tamano, patente, tipo_imagen, pedido):
        font = ImageFont.truetype("./images/Gidole-Regular.ttf", size=12)
        if tipo_imagen == 'LIB':
            img = Image.open('./images/truck_libre.png')
        elif tipo_imagen == 'OFF':
            img = Image.open('./images/truck_off.png')
        elif tipo_imagen == 'PLA':
            img = Image.open('./images/planta.png')
        elif tipo_imagen == 'DES':
            img = Image.open('./images/destino.png')
        elif tipo_imagen == 'SIC':
            img = Image.open('./images/truck_sc.png')
        elif tipo_imagen == 'ENR':
            img = Image.open('./images/truck.png')
        else:
            img = Image.open('./images/sin_imagen.png')

        width, height = img.size

        imdr = ImageDraw.Draw(img)
        if patente is not None or patente!='':
            imdr.text((7, 23), patente, font=font, fill=(0, 0, 0))

        if pedido is not None:
            logging.info(f"Viene con pedido {pedido}")
            imdr.rectangle([0, 0, 100, 17], fill=(255, 255, 255), outline=None, width=1)
            imdr.text((3, 2), pedido, font=font, fill=(0, 0, 0))

        #Tamaño
        #XL = x2, L x1,5 / S /1,5 SX / 2
        if tamano == "S":
            width = int(width / 1.5)
            height = int(height / 1.5)
        elif tamano == "XS":
            width = int(width / 2)
            height = int(height / 2)
        elif tamano == "L":
            width = int(width * 1.5)
            height = int(height * 1.5)
        elif tamano == "XL":
            width = width * 2
            height = height * 2

        newsize = (width, height)
        img = img.resize(newsize)
        img_io = BytesIO() 
        img.save(img_io,'PNG')
        img_io.seek(0)
        return img_io

        ##XS/S/M/L/XL

    @staticmethod
    def getImage(tipo, tamano="M"):
        if tipo == "D": #DESTINO
            img = Image.open('./images/destino.png')
        else:
            img = Image.open('./images/planta.png')

        width, height = img.size

        #Tamaño
        #XL = x2, L x1,5 / S /1,5 SX / 2
        if tamano == "S":
            width = int(width / 1.5)
            height = int(height / 1.5)
        elif tamano == "XS":
            width = int(width / 2)
            height = int(height / 2)
        elif tamano == "L":
            width = int(width * 1.5)
            height = int(height * 1.5)
        elif tamano == "XL":
            width = width * 2
            height = height * 2

        newsize = (width, height)
        img = img.resize(newsize)
        img_io = BytesIO() 
        img.save(img_io,'PNG')
        img_io.seek(0)
        return img_io
