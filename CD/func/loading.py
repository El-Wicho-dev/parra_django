from django.db import transaction
from django.core.mail import send_mail
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.conf import settings
from Documentos.models import Documento,Historial
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import F, Value as V, CharField,Case,When,Q
from django.db.models.functions import Concat, Cast
from Entrenamiento.models import Entrenamiento,EntrenamientoPuestoNomenclatura,Firma
from Documentos.models  import Documento,Plantilla
from Usuarios.models import UnidadNegocio,Puesto,UsuarioPuesto,PerfilUsuario



#@transaction.atomic
def aprobar_entrenamiento(id_documento, nombre_documento, id_usuario):
    print("hola si funciono jeje")
    
    documento = Documento.objects.get(id=id_documento)
    usuario = User.objects.get(id=id_usuario)
            
    try:
        # Actualizar el estado del documento
        liberar_documento = Documento.objects.get(id=id_documento)
        liberar_documento.estado = 'PREAPROBADO'
        liberar_documento.save()

        # Registrar quién aprobó el entrenamiento
        Historial.objects.create(
            id_documento=documento,
            id_responsable=usuario,
            fecha=timezone.now(),
            accion='ENTRENAMIENTO APROBADO'
        )

        """
        # Enviar correo electrónico al responsable del documento
        correo_responsable = User.objects.filter(id_usuario=liberar_documento.id_responsable).values_list('correo', flat=True).first()
        if correo_responsable:
            send_mail(
                'Entrenamiento validado',
                f'El entrenamiento del documento {nombre_documento} fue aceptado. El documento será enviado a revisión por Control de Documentos.',
                settings.DEFAULT_FROM_EMAIL,
                [correo_responsable],
                fail_silently=False,
            )

        # Enviar correo electrónico a los usuarios relevantes
        correos_administradores = User.objects.filter(puestos_empleados__puesto__descripcion_general__icontains='documentos') \
                                                 .filter(estado='ACTIVO') \
                                                 .exclude(correo='') \
                                                 .values_list('correo', flat=True)
        if correos_administradores:
            send_mail(
                'Documento pendiente por liberar',
                f'El documento {nombre_documento} ya fue aprobado por entrenamiento y sellado, por lo que está listo para ser liberado.',
                settings.DEFAULT_FROM_EMAIL,
                list(correos_administradores),
                fail_silently=False,
            )
        """
        # Guardar PDF
        #ruta_pdf = finders.find('PDF_PRELIBERADO')  # Ruta donde se guardarán los PDFs
        #FirmarDocumentos.guardar_pdf(nombre_documento)

    except Exception as e:
        # Manejo de errores
        print(f'Hubo un error al aprobar el entrenamiento: {e}')
        raise


def cargar_documento(id_documento,name_document,id_usuario):
    
    print("hola si funciono en cargar documento ")
    
    documento = Documento.objects.get(id=id_documento)
    usuario = User.objects.get(id=id_usuario)
            
    try:
        # Actualizar el estado del documento
        liberar_documento = Documento.objects.get(id=id_documento)
        liberar_documento.estado = 'APROBADO'
        liberar_documento.fecha_finalizacion = timezone.now()
        liberar_documento.save()

        # Registrar quién aprobó el entrenamiento
        Historial.objects.create(
            id_documento=documento,
            id_responsable=usuario,
            fecha=timezone.now(),
            accion='DOCUMENTO LIBERADO'
        )
        
    except Exception as e:
        # Manejo de errores
        print(f'Hubo un error al aprobar el entrenamiento: {e}')
        raise
    

def rechazar_documento(self):
        try:
            # Mandar correo
            send_mail(
                'Documento rechazado',
                f'El trabajador {self.revisador.username} de Amphenol Otay ha rechazado su archivo {self.nombre} con el comentario: {self.comentarios}',
                settings.EMAIL_HOST_USER,  # Coloca aquí el correo electrónico del remitente
                [self.aprobador.email],  # Lista de correos electrónicos de los destinatarios
                fail_silently=False,
            )

            # Actualizar registro
            self.estado = 'RECHAZADO'
            self.fecha_finalizacion = timezone.now()
            self.save()

            return 1  # Resultado de éxito

        except Exception as e:
            # Manejo de errores
            print(f'Hubo un error al rechazar el documento: {e}')
            return 0  # Resultado de error
        
        
        
def cargar_matriz():
    matriz = []

    # Add columns
    columns = [
        'DEPARTAMENTO', 'AREA', 'NUMERO', 'NOMBRE', 'PUESTO'
    ]

    # Query documents
    documents = (Documento.objects
                 .filter(
                     Q(id_plantilla__nombre='PROCEDIMIENTO') | Q(id_plantilla__nombre='FORMATOS'),
                     estado='APROBADO'
                 )
                 .distinct()
                 .annotate(
                     nomenclatura=Concat(
                         F('id_plantilla__codigo'), V('-'), F('id_linea__codigo_linea'), V(' '),
                         Case(
                             When(consecutivo='00', then=V('00')),
                             When(consecutivo__lt='10', then=Concat(V('0'), F('consecutivo'))),
                             default=F('consecutivo'),
                             output_field=CharField()
                         )
                     )
                 )
                 .order_by('nomenclatura'))

    document_nomenclatures = [doc.nomenclatura for doc in documents]
    columns.extend(document_nomenclatures)
    
    # Print document nomenclatures and documents
    print("Document Nomenclatures:", document_nomenclatures)
    print("Documents:", list(documents))

    total_porcentaje = 0  # Variable para almacenar el porcentaje total

    # Query puestos
    puestos = (Puesto.objects
               .filter(descripcion_general__isnull=False)
               .order_by('id_departamento__id_area__area', 'id_departamento__departamento', 'descripcion_general'))

    # Print puestos
    print("Puestos:", list(puestos))

    for puesto in puestos:
        area = puesto.id_departamento.id_area.area
        departamento = puesto.id_departamento.departamento
        descripcion_general = puesto.descripcion_general
        id_puesto = puesto.id
        por_unidad_negocio = puesto.por_unidad_negocio

        # Print each puesto
        print("Processing Puesto:", puesto)
        
        if por_unidad_negocio:
            # Logic for handling 'por_unidad_negocio'
            row = {
                'DEPARTAMENTO': departamento,
                'AREA': area,
                'PUESTO': descripcion_general,
                'NUMERO': '',
                'NOMBRE': ''
            }

            completed_count = 0  # Contador para entrenamientos completados

            for nomenclatura in document_nomenclatures:
                entrenamiento_puesto_nomenclatura = (EntrenamientoPuestoNomenclatura.objects
                                                     .filter(
                                                         id_puesto=puesto,
                                                         nomenclatura=nomenclatura,
                                                         id_unidad_negocio=puesto.por_unidad_negocio
                                                     )
                                                     .exists())
                row[nomenclatura] = 'X' if entrenamiento_puesto_nomenclatura else 'NA'
                if row[nomenclatura] == 'X':
                    completed_count += 1

            # Calcular porcentaje para el puesto
            total_documents = len(document_nomenclatures)
            row['PORCENTAJE'] = (completed_count / total_documents) * 100 if total_documents > 0 else 0
            total_porcentaje += row['PORCENTAJE']

            # Print row after adding document values for por_unidad_negocio
            print("Row for por_unidad_negocio after adding document values:", row)

            matriz.append(row)

            # Query usuarios
            usuarios = (PerfilUsuario.objects
                        .filter(user__usuariopuesto__puesto=puesto, estado='ACTIVO')
                        .distinct())

            # Print usuarios for por_unidad_negocio
            print(f"Usuarios for Puesto {id_puesto} with por_unidad_negocio:", list(usuarios))

            for usuario in usuarios:
                user_row = row.copy()
                user_row['NUMERO'] = usuario.no_empleado
                user_row['NOMBRE'] = f"{usuario.user.first_name} {usuario.user.last_name}"

                completed_count = 0  # Reiniciar contador para cada usuario

                for nomenclatura in document_nomenclatures:
                    entrenamiento = (Entrenamiento.objects
                                     .filter(
                                         id_documento__estado='APROBADO',
                                         id_usuario=usuario.user,
                                         id_documento__id_plantilla__codigo=nomenclatura.split('-')[0],
                                         id_documento__id_linea__codigo_linea=nomenclatura.split('-')[1].split(' ')[0],
                                         id_documento__consecutivo=nomenclatura.split(' ')[1]
                                     )
                                     .exists())
                    user_row[nomenclatura] = 'C' if entrenamiento else '0'
                    if user_row[nomenclatura] == 'C':
                        completed_count += 1

                # Calcular porcentaje para el usuario
                user_row['PORCENTAJE'] = (completed_count / total_documents) * 100 if total_documents > 0 else 0
                total_porcentaje += user_row['PORCENTAJE']

                # Print user_row after adding user information for por_unidad_negocio
                print("User row for por_unidad_negocio after adding user information:", user_row)

                matriz.append(user_row)
        else:
            row = {
                'DEPARTAMENTO': departamento,
                'AREA': area,
                'PUESTO': descripcion_general,
                'NUMERO': '',
                'NOMBRE': ''
            }

            completed_count = 0  # Contador para entrenamientos completados

            # Add document values
            for nomenclatura in document_nomenclatures:
                entrenamiento_puesto_nomenclatura = (EntrenamientoPuestoNomenclatura.objects
                                                     .filter(
                                                         id_puesto=puesto,
                                                         nomenclatura=nomenclatura
                                                     )
                                                     .exists())
                row[nomenclatura] = 'X' if entrenamiento_puesto_nomenclatura else 'NA'
                if row[nomenclatura] == 'X':
                    completed_count += 1

            # Calcular porcentaje para el puesto
            total_documents = len(document_nomenclatures)
            row['PORCENTAJE'] = (completed_count / total_documents) * 100 if total_documents > 0 else 0
            total_porcentaje += row['PORCENTAJE']

            # Print row after adding document values
            print("Row after adding document values:", row)

            matriz.append(row)

            # Query usuarios
            usuarios = (UsuarioPuesto.objects
                        .filter(puesto=id_puesto)
                        .select_related('usuario', 'usuario__perfilusuario')
                        .values('usuario__first_name', 'usuario__last_name', 'usuario__perfilusuario__no_empleado', 'usuario_id'))

            # Print usuarios
            print(f"Usuarios for Puesto {id_puesto}:", list(usuarios))

            for usuario in usuarios:
                user_row = {
                    'NUMERO': usuario['usuario__perfilusuario__no_empleado'],
                    'NOMBRE': f"{usuario['usuario__first_name']} {usuario['usuario__last_name']}",
                    'DEPARTAMENTO': departamento,
                    'AREA': area,
                    'PUESTO': descripcion_general,
                }

                completed_count = 0  # Reiniciar contador para cada usuario

                for nomenclatura in document_nomenclatures:
                    entrenamiento = (Entrenamiento.objects
                                     .filter(
                                         id_documento__estado='APROBADO',
                                         id_usuario=usuario['usuario_id'],
                                         id_documento__id_plantilla__codigo=nomenclatura.split('-')[0],
                                         id_documento__id_linea__codigo_linea=nomenclatura.split('-')[1].split(' ')[0],
                                         id_documento__consecutivo=nomenclatura.split(' ')[1]
                                     )
                                     .exists())
                    user_row[nomenclatura] = 'C' if entrenamiento else '0'
                    if user_row[nomenclatura] == 'C':
                        completed_count += 1

                # Calcular porcentaje para el usuario
                user_row['PORCENTAJE'] = (completed_count / total_documents) * 100 if total_documents > 0 else 0
                total_porcentaje += user_row['PORCENTAJE']
                
                print(completed_count ,"/", total_documents)


                # Print user_row after adding user information
                print("User row after adding user information:", user_row)

                matriz.append(user_row)

    # Print final matrix and columns
    print("Final Columns:", columns)
    print("Final Matrix:", matriz)

    return {
        'columns': columns,
        'rows': matriz,
        'total_porcentaje': total_porcentaje  # Devolver el porcentaje total calculado
    }

