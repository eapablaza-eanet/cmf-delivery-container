import json
import logging
from app import mgdb, config
import requests
import time

from models.gps.geocore import GEOTransporte

class Safecar:
    __NAME  = "SAFECAR"    
    __FILTRO = ['T ACEVEDO']
    __url   = None
    __user  = None
    __pass  = None

    def __init__(self) -> None:
        self.__url = config['GPS'][f"{self.__NAME}.URL"]
        self.__user = config['GPS'][f"{self.__NAME}.USER"]
        self.__pass = config['GPS'][f"{self.__NAME}.PASSWD"]

    def __get_geopos(self):
        url = f"{self.__url}/j_spring_security_check"
        payload=f"j_username={self.__user}&j_password={self.__pass}&submit=Ingresar&cuentaMaestra=%252F"
        headers = {
        'Origin': self.__url,
        'Content-Type': 'application/x-www-form-urlencoded'
        }
        session = requests.Session()
        response = session.post(url, headers=headers, data=payload)
        
        mili = round(time.time()*1000)
        url = f"{self.__url}/estadoVehiculosSimple/?_={mili}"

        response = session.get(url)

        if response.ok:
            return json.loads(response.text)
        else:
            return None

    def get_geo_camiones(self):
        list_transporte_act = []
        geo_result = self.__get_geopos()
        for geoinfo in geo_result:
            if geoinfo['area'] in self.__FILTRO:
                patente = GEOTransporte.Create(geoinfo, self.__NAME)
                if patente is not None:
                    list_transporte_act.append(patente)

        return list_transporte_act

