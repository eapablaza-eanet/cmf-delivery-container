from app import mgdb,app
from models.gps.geocore import GEOTransporte, Chofer, Direccion, Transporte
import logging
from datetime import date, datetime, timedelta
from models.cmf.ppedido import Turno
from mongoengine.queryset.visitor import Q
import geopy.distance

class DetallePedido(mgdb.EmbeddedDocument):
    Material = mgdb.StringField(required=True)
    Denominacion = mgdb.StringField(required=True)
    UM = mgdb.StringField(required=True)
    Cantidad = mgdb.IntField(required=True)


class Pedido(mgdb.Document):
    Numero = mgdb.IntField(primary_key=True, required=True)
    Status = mgdb.StringField()
    SolicitanteId = mgdb.IntField(required=True)
    Solicitante = mgdb.StringField(required=True)
    IngresadoPor = mgdb.StringField()
    Tramo = mgdb.StringField()
    Direccion = mgdb.ReferenceField(Direccion, required=True)
    FechaDespacho = mgdb.DateTimeField(required=True)
    FechaAct = mgdb.DateTimeField(required=True)
    Turno = mgdb.StringField()
    Glosa = mgdb.StringField()
    GuiaDespacho = mgdb.StringField()
    Entrega = mgdb.StringField()
    DocContable = mgdb.StringField()
    TipoTransporte = mgdb.StringField(max_length=4)
    Transporte = mgdb.StringField()
    Chofer = mgdb.ReferenceField(Chofer)
    Content = mgdb.ListField(mgdb.EmbeddedDocumentField(DetallePedido))

    NO_INICIADO = 'NO INICIADO'
    EN_PREPARACION = 'EN PREPARACION'
    DESPACHADO = 'DESPACHADO'
    EN_RUTA = 'EN RUTA'
    EN_DESTINO = 'EN DESTINO'
    RECIBIDO = 'RECIBIDO'
    ERROR = 'ERROR'

    @staticmethod
    def __status(data_in):
        if data_in['Status'].strip() == '':
            return Pedido.NO_INICIADO
        elif data_in['Status'].strip().upper() == 'A':
            return Pedido.EN_PREPARACION
        elif data_in['Status'].strip().upper() == 'C':
            return Pedido.DESPACHADO
        else:
            logging.error(f"Status no reconocido > '{data_in['Status']}'")
            return Pedido.ERROR

    @staticmethod
    def Create(data_in):
        pedido = Pedido()
        pedido.Numero = int(data_in['Pedido'])
        pedido.Status = Pedido.__status(data_in)
        pedido.Solicitante = data_in['Solicitante'].strip().upper()
        pedido.SolicitanteId = int(data_in['SolicitanteId'])
        pedido.IngresadoPor = data_in['IngresadoPor'].strip()
        pedido.Tramo = data_in['Tramo'].strip()
        pedido.Direccion = Direccion.Read(data_in['Direccion'])
        pedido.Turno = data_in['Turno']

        pedido.TipoTransporte = 'OTRO'
        pedido.FechaDespacho = Turno.get_hora_despacho(
            pedido.Turno, data_in['FechaDespacho'], '')
        pedido.Glosa = data_in['Glosa']
        try:
            if data_in['Glosa'].startswith('PROP') or data_in['Glosa'].startswith('CMF'):
                [tipo, hora] = data_in['Glosa'].split(' ')[0].split('-')
                pedido.TipoTransporte = tipo
                pedido.FechaDespacho = Turno.get_hora_despacho(pedido.Turno, data_in['FechaDespacho'], hora)
        except:
            logging.error(f"Error al procesar Pedido > {pedido.Numero} / Glosa: {data_in['Glosa']} / Fecha Despacho: {data_in['FechaDespacho']}", stack_info=True)

        for ct in data_in['Contenido']:
            depe = DetallePedido()
            depe.Material = ct['Material']
            depe.Denominacion = ct['Denominacion'] 
            depe.UM = ct['UM']
            depe.Cantidad = ct['Cantidad']
            pedido.Content.append(depe)

        pedido.FechaAct = datetime.now()
        pedido.save()

        return pedido

    @staticmethod
    def Update(pedido, data_in):
        pedido.Status = Pedido.__status(data_in)
        pedido.FechaAct = datetime.now()
        pedido.save()
        return pedido

    @staticmethod
    def Update2(pedido, guia_despacho, entrega, doc_contable, patente, chofer):
        pedido = Pedido.objects(Numero=int(pedido)).first()
        if pedido is None:
            return None

        logging.info(f"UPDATE DOCS {pedido.Numero} / {patente} / {chofer}")
        pedido.GuiaDespacho = guia_despacho
        pedido.Entrega = entrega
        pedido.DocContable = doc_contable
        pedido.Transporte = Transporte.Read(patente)
        pedido.Chofer = Chofer.Read(chofer)
        pedido.FechaAct = datetime.now()
        pedido.save()

        return pedido

    @staticmethod
    def procesa_pedido(data_in):
        status = ''
        pedido = Pedido.objects(Numero=int(data_in['Pedido'])).first()
        if pedido is None:
            pedido = Pedido.Create(data_in)
        else:
            pedido = Pedido.Update(pedido, data_in)

        # if status!=pedido.Status:
        DeliveryPedido.seguimiento_pedido(pedido)
        return pedido

    

class EventoDelivery(mgdb.EmbeddedDocument):
    Fecha = mgdb.DateTimeField(required=True)
    Status = mgdb.StringField()
    Informacion = mgdb.StringField()
    Track = mgdb.ReferenceField(GEOTransporte)
    Latitud = mgdb.FloatField()
    Longitud = mgdb.FloatField()

    @staticmethod
    def crea_evento(status, informacion, track=None):
        ev = EventoDelivery()
        ev.Fecha = datetime.now()
        ev.Status = status
        ev.Informacion = informacion
        ev.Track = track
        if track is not None:
            ev.Latitud = track.Latitud
            ev.Longitud = track.Longitud
        return ev


class DeliveryPedido(mgdb.Document):
    Pedido = mgdb.ReferenceField(Pedido, required=True)
    Status = mgdb.StringField(required=True)
    FechaAct = mgdb.DateTimeField(required=True)
    TipoTransporte = mgdb.StringField(max_length=4)
    Transporte = mgdb.StringField()
    Chofer = mgdb.ReferenceField(Chofer)
    Origen = mgdb.ReferenceField(Direccion, required=True)
    Destino = mgdb.ReferenceField(Direccion, required=True)
    Inicio = mgdb.DateTimeField(required=True)
    Fin = mgdb.DateTimeField()
    FechaDespachoOG = mgdb.DateTimeField()
    FechaDespachoReal = mgdb.DateTimeField()
    Latitud = mgdb.FloatField()
    Longitud = mgdb.FloatField()
    Duracion = mgdb.StringField()  # ETA Estimado en palabras desde GEO Transporte
    DuraNumber = mgdb.IntField()  # ETA En segundos desde GEO Transporte
    UltimoTrack = mgdb.ReferenceField(GEOTransporte)
    Tracking = mgdb.ListField(mgdb.ReferenceField(GEOTransporte))

    Eventos = mgdb.ListField(mgdb.EmbeddedDocumentField(EventoDelivery))

    meta = {"indexes": [("Pedido", "Fin")]}

    def CancelarSeguimiento(self, motivo):
        self.FechaAct = datetime.now()
        self.Fin = datetime.now()
        self.Status == Pedido.ERROR
        self.Pedido.Status == Pedido.ERROR
        self.Eventos.append(EventoDelivery.crea_evento(
            self.Status, 'CANCELADO POR USUARIO /'+motivo))
        self.save()
        self.Pedido.save()

    def __NoIniciado(self):
        ya_marcado_en_prepa = False
        if self.Pedido.Status == Pedido.EN_PREPARACION:
            self.AddEvent(Pedido.EN_PREPARACION, 'INICIO TRACKING PEDIDO')
            ya_marcado_en_prepa = True

        if self.Pedido.Status == Pedido.DESPACHADO:
            if not ya_marcado_en_prepa:
                self.AddEvent(Pedido.EN_PREPARACION, 'INICIO TRACKING PEDIDO ASUMIENDO PREPARACIÔN')
            
            self.FechaDespachoReal = datetime.now()
            if self.Transporte is None:
                if self.TipoTransporte == 'CMF':
                    self.AddEvent(
                        Pedido.DESPACHADO, 'SE MARCA DESPACHO, EN ESPERA DE INFORMACIÓN DE TRANSPORTE [*]')
                else:
                    self.AddEvent(
                        Pedido.DESPACHADO, 'DESPACHADO, NO ES TRANSPORTE CMF -> SIN TRACK DE TRANSPORTE [*]', True)
            else:
                self.AddEvent(Pedido.DESPACHADO,
                                'DESPACHADO, SE INICIA TRACKING DE TRANSPORTE [*]')

    def __EnPreparacion(self):
        if self.Pedido.Status == Pedido.EN_PREPARACION:
            pass
        elif self.Pedido.Status == Pedido.DESPACHADO:
            self.FechaDespachoReal = datetime.now()
            if self.Transporte is None:
                if self.TipoTransporte == 'CMF':
                    self.AddEvent(
                        Pedido.DESPACHADO, 'SE MARCA DESPACHO, EN ESPERA DE INFORMACIÓN DE TRANSPORTE')
                else:
                    self.AddEvent(
                        Pedido.DESPACHADO, 'DESPACHADO, NO ES TRANSPORTE CMF -> SIN TRACK DE TRANSPORTE', True)
            else:
                self.AddEvent(Pedido.DESPACHADO,
                                'DESPACHADO, SE INICIA TRACKING DE TRANSPORTE')

    def EnTiempoEsperaPatente(self, fecha_despacho_real):
        fecha_corte = fecha_despacho_real + \
            timedelta(minutes=float(app.config.get('MAX_MIN_ESPERA_PATENTE')))
        return datetime.now() <= fecha_corte

    def __Despachado(self):
        if self.Transporte is None:

            if self.FechaDespachoReal is None:
                self.FechaDespachoReal = self.FechaDespachoOG

            if self.EnTiempoEsperaPatente(self.FechaDespachoReal):
                logging.info(
                    f"Esperando la Patente / Chofer para Pedido {self.Pedido.Numero}")
            else:
                self.AddEvent(
                    Pedido.DESPACHADO, 'SE FINALIZA TRACK, SE AGOTÒ TIEMPO ESPERA DE INFORMACIÒN DE PATENTE / CHOFER', True)
        else:
            ul_tr = GEOTransporte.get_tranporte_actual(self.Transporte)
            if ul_tr is None:
                if self.TipoTransporte == 'CMF':
                    self.AddEvent(Pedido.ERROR, f'SE FINALIZA TRACK, por inexistencia de GPS en Transporte o Error en Captura', True)
                else:
                    self.AddEvent(Pedido.DESPACHADO, f'SE FINALIZA TRACK, por inexistencia de Seguimiento GPS en Transporte', True)
            else:

                ul_tr.CalculaETA(self.Destino)
                if ul_tr not in self.Tracking:
                    self.Tracking.append(ul_tr)

                if not ul_tr.EnPlanta:
                    self.AddEvent(
                        Pedido.EN_RUTA, 'TRANSPORTE YA EN RUTA', False, ul_tr)

    def __EnRuta(self):
        ul_tr = GEOTransporte.get_tranporte_actual(self.Transporte)
        if ul_tr is None:
            self.AddEvent(
                Pedido.ERROR, 'SE FINALIZA TRACK, Sin información de GPS en RUTA', True)
            return

        ul_tr.CalculaETA(self.Destino)
        if ul_tr not in self.Tracking:
            self.Tracking.append(ul_tr)

        if ul_tr.EnDestino:  # Si ya llegó debo cambiar estado
            self.AddEvent(Pedido.EN_DESTINO,
                            'TRANSPORTE LLEGA A DESTINO', False, ul_tr)
        elif ul_tr.EnPlanta:
            self.AddEvent(
                Pedido.ERROR, 'TRANSPORTE VUELVE A PLANTA Y NO SE CAPTURÓ LA LLEGADA A DESTINO', False, ul_tr)

    def __EnDestino(self):
        ul_tr = GEOTransporte.get_tranporte_actual(self.Transporte)
        if ul_tr is None:
            self.AddEvent(
                Pedido.ERROR, 'SE FINALIZA TRACK, Sin información de GPS en DESTINO', True)
            return

        ul_tr.CalculaETA(self.Destino)

        if not ul_tr.EnDestino:  # Si ya no está en planta se cambia estado.
            self.AddEvent(
                Pedido.RECIBIDO, 'TRANSPORTE DEJA DESTINO / ENTREGA REALIZADA', True, ul_tr)
        elif ul_tr.EnPlanta:
            self.AddEvent(
                Pedido.ERROR, 'ERROR EN TRACK, NO SE CAPTURA SALIDA DE DESTINO', True, ul_tr)

    def SetUbicacionYTrack(self):
        # Si ya está cerrado no hay nada que hacer
        if self.Fin is not None:
            return

        # Actualizo los datos del Pedido en el Delivery
        self.Transporte = self.Pedido.Transporte
        self.Chofer = self.Pedido.Chofer
        self.FechaDespachoOG = self.Pedido.FechaDespacho
        self.FechaAct = datetime.now()

        # Cuando el pedido está en preparación no hay mucho que hacer, solo esperar siguiente informe
        if self.Status == Pedido.NO_INICIADO:
            self.__NoIniciado()
        elif self.Status == Pedido.EN_PREPARACION:
            self.__EnPreparacion()
        elif self.Status == Pedido.DESPACHADO:
            self.__Despachado()
        elif self.Status == Pedido.EN_RUTA:
            self.__EnRuta()
        elif self.Status == Pedido.EN_DESTINO:
            self.__EnDestino()

        self.save()
        self.Pedido.save()

    def AddEvent(self, status, text_desc, es_fin=False, posGeo=None):

        self.Status = status
        self.FechaAct = datetime.now()
        self.Pedido.Status = status
        self.Pedido.FechaAct = datetime.now()

        if es_fin:
            self.Fin = datetime.now()

        if posGeo is not None:
            self.Latitud = posGeo.Latitud
            self.Longitud = posGeo.Longitud
            self.Duracion = posGeo.Duracion
            self.DuraNumber = posGeo.DuraNumber
            self.UltimoTrack = posGeo
            if posGeo not in self.Tracking:
                self.Tracking.append(posGeo)

        self.Eventos.append(EventoDelivery.crea_evento(
            self.Status, text_desc, posGeo))

        self.Pedido.save()
        self.save()

    @staticmethod
    def __Create(pedido: Pedido):
        de_pe = DeliveryPedido()
        de_pe.Pedido = pedido
        de_pe.Status = pedido.Status
        de_pe.FechaAct = datetime.now()
        de_pe.TipoTransporte = pedido.TipoTransporte
        de_pe.Transporte = pedido.Transporte
        de_pe.Chofer = pedido.Chofer
        de_pe.Origen = Direccion.Planta()
        de_pe.Destino = pedido.Direccion
        de_pe.Inicio = datetime.now()
        de_pe.FechaDespachoOG = pedido.FechaDespacho
        return de_pe

    @staticmethod
    def seguimiento_pedido(pedido: Pedido):
        logging.info(f"seguimiento_pedido > INI : {pedido.Numero}")
        if pedido.Status == Pedido.NO_INICIADO:
            logging.info(f"Pedido {pedido.Numero}, TODAVIA NO INICIA")
            return

        ped_seg = DeliveryPedido.objects(Pedido=pedido).first()
        if ped_seg is None:
            ped_seg = DeliveryPedido.__Create(pedido)
        else:
            if ped_seg.Fin is not None:
                logging.info(f"Pedido {pedido.Numero} con TRACKING CERRADO")
                return

        ped_seg.SetUbicacionYTrack()
        logging.info(f"seguimiento_pedido > FIN : {pedido.Numero}")

    @staticmethod
    def input_info_ventas(data):
        total = 0
        Ok = 0
        NOk = 0

        for dave in data:
            total += 1
            try:
                Pedido.procesa_pedido(dave)
                Ok += 1
            except Exception as e:
                NOk += 1
                logging.error(f"Error al procesar Pedido {dave['Pedido']}")
                logging.error(e)

        return {"Procesados": total, "OK": Ok, "NOK": NOk}

    @staticmethod
    def input_info_fact(data):
        total = 0
        Ok = 0
        NOk = 0

        for fv in data:
            try:
                total += 1
                pe_upd = Pedido.Update2(
                    fv['Pedido'], fv['GuiaDespacho'], fv['Entrega'], fv['DocContable'], fv['Patente'], fv['Chofer'])
                if pe_upd is not None:
                    DeliveryPedido.seguimiento_pedido(pe_upd)
                Ok += 1
            except Exception as e:
                NOk += 1
                logging.error(f"Error al procesar Docs Pedido {fv}")
                logging.error(e)

        return {"Procesados": total, "OK": Ok, "NOK": NOk}

    @staticmethod
    def ProcesaDelivery(lst_patentes):
        lista_procesada = []
        for pat in lst_patentes:
            logging.info(f"Procesando Pantente: {pat}")
            transporte = Transporte.Read(pat)

            de_pe = DeliveryPedido.objects(
                Fin=None, Transporte=transporte).order_by('-Inicio')
            if de_pe.count() == 1:
                de_pe = de_pe.first()
            elif de_pe.count() == 0:
                de_pe = None
            else:
                primero = de_pe.first()
                for depe in de_pe:
                    if depe.Pedido != primero.Pedido:
                        depe.Fin = datetime.now()
                        depe.FechaAct = datetime.now()
                        depe.Status = Pedido.ERROR
                        depe.Eventos.append(EventoDelivery.crea_evento(
                            depe.Status, f'ERROR, Mas de un pedido = Patente {pat}, Se conserva {primero.Pedido.Numero}'))
                        depe.save()
                de_pe = primero

            if de_pe is not None:
                logging.info(
                    f"Transporte > {pat} con Pedido > {de_pe.Pedido.Numero}")
                de_pe.SetUbicacionYTrack()
                lista_procesada.append(transporte)
            else:
                logging.info(f"Transporte > {pat} SIN PEDIDO")

        logging.info("FIN PROCESO PATENTES")
        return lista_procesada

    @staticmethod
    def FechaCorteGPS():
        return datetime.now()-timedelta(minutes=10)

    @staticmethod
    def TransportesEnPlanta():
        return DeliveryPedido.StatusTransporte(False, False, True, False, False)

    @staticmethod
    def getDelivery(patente):
        return DeliveryPedido.objects(Q(Fin=None) & Q(Transporte=patente)).order_by('-FechaAct').first()

    @staticmethod
    def GetStatusTransporte(patente, t='M'):
        baseUrl = config['API']['BASE_URL'] + \
            config['API']['Version']+'/transporte/imagen?'

        status_patente = GEOTransporte.get_tranporte(patente)

        if not status_patente.EstaActivo:
            ult_info = status_patente.FechaGPS.strftime('%d-%m-%Y %H:%M:%S')
            return {
                        "type" : "SinConexion",
                        "location": [status_patente.Latitud, status_patente.Longitud],
                        "tooltip": {
                            "text": f"<strong>{patente}<br/>Sin Conexion</strong><br/>Última Información Recibida {ult_info}"
                        },
                        "Patente": patente,
                        "iconSrc": f"{baseUrl}p={patente}&t={t}&ti=SIC"
                    }
        
        if status_patente.Motor == 'APAGADO':
            return {
                        "type" : "Detenido",
                        "location": [status_patente.Latitud, status_patente.Longitud],
                        "tooltip": {
                            "text": f"<strong>{patente}<br/>Detenido</strong>"
                        },
                        "Patente": patente,
                        "iconSrc": f"{baseUrl}p={patente}&t={t}&ti=OFF"
                    }
        
        #Aqui debo buscar es que esta el camión
        depe = DeliveryPedido.getDelivery(patente)
        if depe is None:
            if status_patente.EnPlanta:
                return {
                            "type" : "EnPlanta",
                            "location": [status_patente.Latitud, status_patente.Longitud],
                            "tooltip": {
                                "text": f"<strong>{patente}<br/>En Planta</strong>"
                            },
                            "Patente": patente,
                            "iconSrc": f"{baseUrl}p={patente}&t={t}&ti=LIB"
                        }
            else: #Si viene retornando de un pedido o a ubicarse a la planta
                return {
                            "type" : "EnRetorno",
                            "location": [status_patente.Latitud, status_patente.Longitud],
                            "tooltip": {
                                "text": f"<strong>{patente}<br/>Disponible</strong><br/>A {status_patente.ETAPlanta} de la Planta."
                            },
                            "Patente": patente,
                            "iconSrc": f"{baseUrl}p={patente}&t={t}&ti=LIB"
                        }

        else:
            duracion = ''
            if status_patente.Duracion is not None:
                duracion = f"<br/>A {status_patente.Duracion} del Destino"

            pedido = f"<br/>Con Pedido: <strong>{depe.Pedido.Numero}</strong><br/>Cliente: {depe.Pedido.Solicitante}" 
            return {
                        "type" : "EnEntrega",
                        "location": [status_patente.Latitud, status_patente.Longitud],
                        "tooltip": {
                            "text": f"<strong>{patente}<br/>{depe.Status}</strong>{duracion}{pedido}"
                        },
                        "Patente": patente,
                        "Pedido": depe.Pedido.Numero,
                        "DeliveryId": str(depe.id),
                        "iconSrc": f"{baseUrl}p={patente}&t={t}&ti=ENR&pe={depe.Pedido.Numero}"
                    }

    @staticmethod
    def StatusTransporteByPatente(patente, t):
        status = []
        st_pa = DeliveryPedido.GetStatusTransporte(patente, t)
        status.append(st_pa)
        return status

    @staticmethod
    def StatusTransporte(sin_conexion, detenidos, en_planta, en_entrega, en_retorno, t):
        patentes = GEOTransporte.get_patentes()

        status = []
        for patente in patentes:
            st_pa = DeliveryPedido.GetStatusTransporte(patente, t)
            
            if st_pa['type'] == 'SinConexion' and sin_conexion:
                status.append(st_pa)
            elif st_pa['type'] == 'Detenido' and detenidos:
                status.append(st_pa)
            elif st_pa['type'] == 'EnPlanta' and en_planta:
                status.append(st_pa)
            elif st_pa['type'] == 'EnRetorno' and en_retorno:
                status.append(st_pa)
            elif st_pa['type'] == 'EnEntrega' and en_entrega:
                status.append(st_pa)

        return status

    @staticmethod
    def DeliverysEnCurso():
        response = []
        for depe in DeliveryPedido.objects(Fin=None).order_by('-FechaDespachoOG'):
            response.append(depe.toJson())

        return response

    def toJson(self):
        chofer = None
        if self.Chofer is not None:
            chofer = self.Chofer.Nombre

        eta = None
        if self.Status == Pedido.EN_RUTA:
            eta = self.Duracion

        fecha_despacho_real = None
        diff_despacho = 0
        if self.FechaDespachoReal is not None:
            fecha_despacho_real = self.FechaDespachoReal.isoformat()
            if self.FechaDespachoReal > self.Pedido.FechaDespacho:
                diff_despacho = int(
                    (self.FechaDespachoReal - self.Pedido.FechaDespacho).total_seconds())

        elif datetime.now() > self.Pedido.FechaDespacho:
            fecha_despacho_real = datetime.now().isoformat()
            diff_despacho = int(
                (datetime.now() - self.Pedido.FechaDespacho).total_seconds())

        data = {
            "Id": str(self.id),
            "Pedido": self.Pedido.Numero,
            "Status": self.Status,
            "FechaAct": self.FechaAct.isoformat(),
            "Transporte": self.Transporte,
            "TipoTransporte": self.TipoTransporte,
            "Chofer": chofer,
            "Destino": self.Destino.formatted_address,
            "ETA": eta,
            "Solicitante": self.Pedido.Solicitante,
            "SolicitanteId": self.Pedido.SolicitanteId,
            "FechaDespacho": self.Pedido.FechaDespacho.isoformat(),
            "FechaDespachoReal": fecha_despacho_real,
            "DiffDespacho": diff_despacho,
            "Turno": self.Pedido.Turno
        }
        return data

    def toJsonDetail(self):
        base = self.toJson()

        base['Origen'] = [self.Origen.Latitud, self.Origen.Longitud]
        base['Destino'] = [self.Destino.Latitud, self.Destino.Longitud]

        if self.Latitud is None:
            planta = Direccion.Planta()
            base['Actual'] = [planta.Latitud, planta.Longitud]
        else:
            base['Actual'] = [self.Latitud, self.Longitud]

        base['Eventos'] = []
        for rv in self.Eventos:
            base['Eventos'].append(
                {
                    "Fecha": rv.Fecha.isoformat(),
                    "Status": rv.Status,
                    "Informacion": rv.Informacion
                }
            )

        base['Track'] = []
        for trk in self.Tracking:
            base['Track'].append(
                {
                    "id": str(trk.id),
                    "FechaGPS": trk.FechaGPS.isoformat(),
                    "Orientacion": trk.Orientacion,
                    "Position": [trk.Latitud, trk.Longitud],
                    "Status": trk.Status,
                    "EstadoMov": trk.EstadoMov
                }
            )

        base['Pedido'] = {
            "Numero": self.Pedido.Numero,
            "SolicitanteId": self.Pedido.SolicitanteId,
            "Solicitante": self.Pedido.Solicitante,
            "IngresadoPor": self.Pedido.IngresadoPor,
            "Tramo": self.Pedido.Tramo,
            "Direccion": self.Pedido.Direccion.formatted_address,
            "FechaDespacho": self.Pedido.FechaDespacho.isoformat(),
            "Turno": self.Pedido.Turno,
            "Glosa": self.Pedido.Glosa,
            "GuiaDespacho": self.Pedido.GuiaDespacho,
            "Entrega": self.Pedido.Entrega,
            "DocContable": self.Pedido.DocContable,
            "TipoTransporte": self.Pedido.TipoTransporte,
            "Transporte": self.Pedido.Transporte,
            "Chofer": base['Chofer'],
            "Contenido": []
        }

        for cnt in self.Pedido.Content:
            base['Pedido']['Contenido'].append({
                "Material": cnt.Material,
                "Denominacion": cnt.Denominacion,
                "UM": cnt.UM,
                "Cantidad": cnt.Cantidad
            })

        return base

    @staticmethod
    def get_by_pos(lat, lng, t):
        truck_found = GEOTransporte.objects(Latitud=lat, Longitud = lng).order_by('-FechaGPS').first()
        if truck_found is None:
            dist = 10000000
            pos_ini = (lat,lng)
            for patente in GEOTransporte.get_patentes():
                tf = GEOTransporte.objects(Transporte=patente).order_by('-FechaGPS').first()
                if geopy.distance.geodesic(pos_ini, (tf.Latitud, tf.Longitud)).meters < dist:
                    dist = geopy.distance.geodesic(pos_ini, (tf.Latitud, tf.Longitud)).meters
                    truck_found = tf

        
        if truck_found is None:
            return {}

        stts_trsnprt = DeliveryPedido.GetStatusTransporte(truck_found.Transporte, t)
        if 'DeliveryId' in stts_trsnprt:
            de_pe = DeliveryPedido.objects(id=stts_trsnprt['DeliveryId']).first()
            if de_pe is not None:
                stts_trsnprt['Delivery'] = de_pe.toJsonDetail()

        return stts_trsnprt

    @staticmethod
    def mantencion_db():
        cerrados = []
        fecha = datetime.now()-timedelta(days=1)
        for de_del in DeliveryPedido.objects(Fin=None, FechaDespachoOG__lt=fecha):
            de_del.AddEvent(Pedido.ERROR, 'Seguimiento dura mas de 1 lo establecido', es_fin=True)
            cerrados.append({ "Pedido": de_del.Pedido.Numero })

        return cerrados         
    
    @staticmethod
    def Informe(fecha_inicio, fecha_fin, con_error=False):
        try:
            fInicio = datetime.fromisoformat(fecha_inicio) #, '%d-%m-%y %H:%M:%S') 
            fFin = datetime.fromisoformat(fecha_fin) 
        except:
            return { "msg": "Error al procesar fechas"}

        reporte = []

        for depe in DeliveryPedido.objects(FechaDespachoOG__gte=fInicio, FechaDespachoOG__lte=fFin):
            EnPreparacion   = None
            T_EnPreparacion = None
            Despachado      = None
            T_Despacho      = None
            AbandonaPlanta  = None
            T_Trayecto      = None
            EnDestino       = None
            T_EnDestino     = None
            Recibido        = None
            T_Total         = None
            ConError        = None

            for ev in depe.Eventos:
                if ev.Status == Pedido.EN_PREPARACION and EnPreparacion is None:
                    EnPreparacion = ev.Fecha
                elif ev.Status == Pedido.DESPACHADO and Despachado is None:
                    Despachado = ev.Fecha
                elif ev.Status == Pedido.EN_RUTA and AbandonaPlanta is None:
                    AbandonaPlanta = ev.Fecha
                elif ev.Status == Pedido.EN_DESTINO and EnDestino is None:
                    EnDestino = ev.Fecha
                elif ev.Status == Pedido.RECIBIDO and Recibido is None:
                    Recibido = ev.Fecha
                else:
                    ConError = ev.Fecha

            #Pedido con error
            if ConError is not None and not con_error:
                continue
            
            if EnPreparacion is not None and Despachado is not None:
                T_EnPreparacion = (Despachado - EnPreparacion).total_seconds() / 60

            if AbandonaPlanta is not None and Despachado is not None:
                T_Despacho = (AbandonaPlanta - Despachado).total_seconds() / 60
            
            if AbandonaPlanta is not None and EnDestino is not None:
                T_Trayecto = (EnDestino - AbandonaPlanta).total_seconds() / 60

            if Recibido is not None and EnDestino is not None:
                T_EnDestino = (Recibido - EnDestino).total_seconds() / 60

            if Recibido is not None and EnPreparacion is not None:
                T_Total = (Recibido - EnPreparacion).total_seconds() / 60

            if EnPreparacion is not None:
                EnPreparacion = EnPreparacion.isoformat()

            if Despachado is not None:
                Despachado = Despachado.isoformat()

            if AbandonaPlanta is not None:
                AbandonaPlanta = AbandonaPlanta.isoformat()

            if EnDestino is not None:
                EnDestino = EnDestino.isoformat()

            if Recibido is not None:
                Recibido = Recibido.isoformat()


            reporte.append(
                {
                    "Pedido"        : depe.Pedido.Numero,
                    "Solicitante"   : depe.Pedido.Solicitante,
                    "Status"        : depe.Status,
                    "Tramo"         : depe.Pedido.Tramo,
                    "Direccion"     : depe.Pedido.Direccion.Direccion,
                    "FechaDespacho" : depe.Pedido.FechaDespacho,
                    "Turno"         : depe.Pedido.Turno,
                    "TipoTransporte": depe.Pedido.TipoTransporte,
                    "Track"         :
                    {
                        "EnPreparacion" : EnPreparacion,
                        "T_EnPreparacion" : T_EnPreparacion,
                        
                        "Despachado" : Despachado,
                        "T_Despacho" : T_Despacho,
                        
                        "AbandonaPlanta" : AbandonaPlanta,
                        "T_Trayecto" : T_Trayecto,

                        "EnDestino" : EnDestino,
                        "T_EnDestino" : T_EnDestino,

                        "Recibido" : Recibido,
                        "T_Total" : T_Total
                    }
                }
            ) 

    
        return reporte