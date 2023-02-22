import logging
from datetime import datetime, timedelta
from app import mgdb, gmaps
from models.gps.transporte import Transporte
from mongoengine.queryset.visitor import Q

class Direccion(mgdb.Document):
    Direccion       = mgdb.StringField(unique=True, required=True)
    Latitud         = mgdb.FloatField() 
    Longitud        = mgdb.FloatField()   
    place_id        = mgdb.StringField()
    formatted_address = mgdb.StringField()
    EsPlanta        = mgdb.BooleanField(required=True) 
   
    @staticmethod
    def Planta():
        dir = Direccion.objects(EsPlanta=True).first()
        if dir is None:
            logging.error(f"###### NO ESTA DEFINIDA LA DIRECCION DE LA PLANTA CMF (Direccion) #########")

        return dir

    @staticmethod
    def Read(direccion):
        dir = Direccion.objects(Direccion=direccion).first()
        if dir is None:
            dir = Direccion(Direccion=direccion, EsPlanta = False)
            dir.BuscaGeoReferencia(True)
            #dir.save()
        elif dir.place_id is None:
            dir.BuscaGeoReferencia()

        return dir
    
    def BuscaGeoReferencia(self, force = False):
        if self.place_id is not None and not force:
            return

        geocode_result = gmaps.geocode(self.Direccion)
        if len(geocode_result) == 1:
            dir_save = geocode_result[0]
        else:
            logging.error(f"No se puede determinar dirección > {self.Direccion}")
            logging.error(geocode_result)
            self.Latitud = None
            self.Longitud = None
            self.place_id = None
            self.formatted_address = None
            self.save()
            return
        
        #Verificando que es Chile
        for adco in dir_save['address_components']:
            if 'country' in adco['types']:
                if adco['short_name'] != 'CL':
                    logging.error(f"Mala detección de dirección > {self.Direccion}")
                    logging.error(geocode_result)
                    self.Latitud = None
                    self.Longitud = None
                    self.place_id = None
                    self.formatted_address = None
                    self.save()
                    return

        self.Latitud = dir_save['geometry']['location']['lat']
        self.Longitud = dir_save['geometry']['location']['lng']
        self.place_id = dir_save['place_id']
        self.formatted_address = dir_save['formatted_address']
        self.save()
   

class Chofer(mgdb.Document):
    Nombre         = mgdb.StringField(required=True)
    #ApellidoPaterno = mgdb.StringField(required=True)
    #ApellidoMaterno = mgdb.StringField(required=True)
    
    @staticmethod
    def Read(nombre):
        ch = Chofer.objects(Nombre=nombre).first()
        if ch is None:
            ch = Chofer(Nombre=nombre)
            ch.save()
            return ch
        else:
            return ch


class GEOTransporte(mgdb.Document):
    Transporte  = mgdb.StringField(required=True)
    FechaGPS    = mgdb.DateTimeField(required=True)
    Chofer      = mgdb.ReferenceField(Chofer)
    From        = mgdb.StringField(max_length=10)
    FechaRecep  = mgdb.DateTimeField(required=True)
    Latitud     = mgdb.FloatField(required=True) 
    Longitud    = mgdb.FloatField(required=True)   
    Status      = mgdb.BooleanField(required=True)   
    Orientacion = mgdb.IntField()   
    EstadoMov   = mgdb.StringField()
    Velocidad   = mgdb.IntField()   
    MmensajeAlarma = mgdb.StringField()
    Alarmado    = mgdb.BooleanField(required=True)   
    MotorBloqueado = mgdb.BooleanField(required=True)
    Odometro    = mgdb.IntField()
    Horometro   = mgdb.IntField()
    Motor       = mgdb.StringField()
    Destino     = mgdb.ReferenceField(Direccion)
    DirDestino  = mgdb.StringField()
    DirActual   = mgdb.StringField()
    Distancia   = mgdb.StringField()
    DistNumber  = mgdb.IntField()
    Duracion    = mgdb.StringField()
    DuraNumber  = mgdb.IntField()
    ResumenRuta = mgdb.StringField()
    PuntosRuta  = mgdb.StringField()
    EnDestino   = mgdb.BooleanField()

    meta = {"indexes": [("Transporte","-FechaGPS")]}

    __TIME_EN_DESTINO = 5.5*60
    __ERROR_EN_GPS    = 15*60   #15 minutos los maximo de error en lectura de GPS, despues de eso se toma como info pasada

    @staticmethod
    def get_patentes():
        patentes = []
        for data in GEOTransporte.objects.only('Transporte').distinct('Transporte'):
            patentes.append(data)
        return patentes

    @staticmethod
    def get_tranporte_actual(transporte):
        ult_info = GEOTransporte.get_tranporte(transporte)
        if ult_info is None:
            return None

        if not ult_info.EstaActivo:
            return None

        return ult_info
    
    @staticmethod
    def get_tranporte(transporte):
        ult_info = GEOTransporte.objects(Transporte=transporte).order_by("-FechaGPS").first()
        if ult_info is None:
            return None

        ult_info.EstaActivo = (datetime.now()-ult_info.FechaGPS).seconds <= GEOTransporte.__ERROR_EN_GPS
        return ult_info

    @staticmethod
    def __get_entrada(key, entradas):
        for ent in entradas.split(';'):
            key_data = (ent.split(':')[0]).strip()
            if key_data == key:
                return (ent.split(':')[1]).strip()
        return None

    @staticmethod
    def Create(data, desde):
        gepa = GEOTransporte()

        patente_find = Transporte.Read(data['patente'])
        if patente_find is None:
            logging.error(f"No se puede ingresar el registro porque la patente es incorrecta > {data['patente']}")
            return None

        try:
            fecha_gps   = datetime.strptime(data['fechaGps'], '%d-%m-%y %H:%M:%S') 
            if GEOTransporte.objects(Transporte=patente_find, FechaGPS = fecha_gps).count()>0:
                return None

            gepa.Transporte = patente_find
            gepa.From   = desde
            gepa.FechaGPS   = fecha_gps
            gepa.FechaRecep = datetime.now() 
            gepa.Latitud    = float(data['latitud'])
            gepa.Longitud   = float(data['longitud'])
            gepa.Status     = data['status']
            gepa.Orientacion    = int(data['orientacion'])
            gepa.EstadoMov  = data['estadoMovimiento']
            gepa.Velocidad  = int(data['velocidad'])
            gepa.MmensajeAlarma = data['mensajeAlarma']
            gepa.Alarmado   = data['alarmado']  
            gepa.MotorBloqueado = data['motorBloqueado']  
            gepa.Motor      = GEOTransporte.__get_entrada('MOTOR', data['entradas'])
            gepa.Odometro   = int(data['odometro']) 
            gepa.Horometro  = int(data['horometro']) 
            gepa.save()
            return gepa.Transporte

        except Exception as e:
            logging.error(e, exc_info=True)
            return None
    
    @property
    def LatLng(self):
        return f"{self.Latitud},{self.Longitud}"

    @property
    def EnPlanta(self):
        now = datetime.now()
        directions_result = gmaps.directions(self.LatLng,
                                    f"place_id:{Direccion.Planta().place_id}",
                                    mode="driving",
                                    language="es",
                                    traffic_model='best_guess',
                                    units='metric',
                                    departure_time=now)
        
        dura = directions_result[0]['legs'][0]['duration']['value']
        return (dura <= self.__TIME_EN_DESTINO)

    @property
    def ETAPlanta(self):
        now = datetime.now()
        directions_result = gmaps.directions(self.LatLng,
                                    f"place_id:{Direccion.Planta().place_id}",
                                    mode="driving",
                                    language="es",
                                    traffic_model='best_guess',
                                    units='metric',
                                    departure_time=now)

        return directions_result[0]['legs'][0]['duration']['text']

    def CalculaETA(self, direccion:Direccion):
        if self.Destino is not None:
            return

        if direccion.place_id is None:
            direccion.BuscaGeoReferencia(True)
            direccion.save()

        now = datetime.now()
        logging.info(f"Calcula ETA {self.Transporte} / {self.LatLng} / {direccion.place_id}")
        directions_result = gmaps.directions(self.LatLng,
                                    f"place_id:{direccion.place_id}",
                                    mode="driving",
                                    language="es",
                                    traffic_model='best_guess',
                                    units='metric',
                                    departure_time=now)
        
        result = directions_result[0]
        self.Destino     = direccion
        self.DirDestino  = result['legs'][0]['end_address']
        self.DirActual   = result['legs'][0]['start_address']
        self.Distancia   = result['legs'][0]['distance']['text']
        self.DistNumber  = result['legs'][0]['distance']['value']
        self.Duracion    = result['legs'][0]['duration']['text']
        self.DuraNumber  = result['legs'][0]['duration']['value']
        self.ResumenRuta = result['summary']
        self.PuntosRuta  = result['overview_polyline']['points']
        self.EnDestino   = (self.DuraNumber <= self.__TIME_EN_DESTINO)
        self.save()               

    @staticmethod
    def mantencion_db():
        fecha = datetime.now()-timedelta(days=1)
        docs = GEOTransporte.objects(Q(FechaGPS__lt = fecha) & Q(DirActual=None)).delete()
        return {'Eliminados': docs, 'FechaCorte': fecha.isoformat() }        

    def calcula_ruta_a(self, EsPla):
        #agregar marker de planta
        #agregar marker destino
        #ruta
        pass