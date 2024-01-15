from datetime import datetime

class ReporteDeExpediente:
    def _init_(self):
        self.NumeroExpediente = None
        self.OrganoJurisdiccional = None
        self.DistritoJudicial = None
        self.Juez = None
        self.EspecialistaLegal = None
        self.FechaInicio = None
        self.Proceso = None
        self.Observacion = None
        self.Especialidad = None
        self.Materias = None
        self.Estado = None
        self.EtapaProcesal = None
        self.FechaConclucion = None
        self.Ubicacion = None
        self.MotivoConclucion = None
        self.Sumilla = None


class ParteProceso:
    def _init_(self):
        self.Rol = None
        self.TipoPersona = None
        self.ApellidoPaterno = None
        self.ApellidoMaterno = None
        self.NombresORazonSocial = None

class Seguimiento:
    def _init_(self):
        self.NumeroEsquina = 0  # Inicializado con 0 ya que es un entero
        self.FechaResolucion = datetime.min  # Inicializado con una fecha mínima
        self.Resolucion = None
        self.TipoNotificacion = None
        self.Acto = None
        self.Fojas = 0  # Inicializado con 0 ya que es un entero
        self.FechaProveido = datetime.min  # Inicializado con una fecha mínima
        self.Sumilla = None
        self.DescripcionUsuario = None
        self.EnlaceDescarga = None
        self.Notificaciones = []  # Lista para almacenar objetos Notificacion

class Notificacion:
    def _init_(self):
        self.Destinatario = None
        self.Anexos = None
        self.FechaResolucion = datetime.min
        self.FechaNotificacionImpresa = datetime.min
        self.FechaEnviadaCentralNotificacion = datetime.min
        self.FechaRecepcionadaCentralNotificacion = datetime.min
        self.FechaNotificacionDestinatario = datetime.min
        self.FechaCargoDevueltoJuzgado = datetime.min
        self.FormaEntrega = None

