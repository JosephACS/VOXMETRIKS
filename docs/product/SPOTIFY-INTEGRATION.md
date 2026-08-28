# Spotify en VOXMETRIKS

## Qué resuelve

Spotify no reemplaza la base de datos ni la inteligencia de VOXMETRIKS. La
conexión autorizada por cada usuario aporta tres señales de gusto: canciones más
escuchadas, reproducciones recientes y biblioteca guardada. VOXMETRIKS relaciona
esos identificadores con su catálogo, combina similitud musical, historial,
favoritos, popularidad y afinidad de artista o género, y devuelve una mezcla
explicable y reproducible.

El orden es:

1. Spotify entrega señales autorizadas del usuario.
2. VOXMETRIKS encuentra coincidencias en su catálogo de aproximadamente 89 mil
   canciones.
3. El motor propio ordena canciones cercanas y explica por qué recomienda cada
   una.
4. El reproductor usa Spotify cuando la cuenta está conectada y la canción tiene
   una coincidencia de Spotify.
5. Si Spotify no está conectado o no puede reproducir la coincidencia, la app
   muestra una explicación clara y permite elegir otra versión; no cambia a un
   proveedor de video oculto.

No se usa el endpoint clásico `GET /recommendations`: Spotify lo retiró para las
aplicaciones nuevas en Development Mode. Por eso la función se llama
**Spotify + VOXMETRIKS** y no finge ser una recomendación oficial de Spotify.

## Configuración local

1. Crear una aplicación en Spotify for Developers.
2. Registrar exactamente `http://127.0.0.1:4200/integrations/spotify/callback`
   como Redirect URI.
3. Instalar el Client ID público una sola vez en la configuración de despliegue
   de VOXMETRIKS (`environment.spotifyClientId`).
4. Abrir **Configuración > Música conectada** y pulsar **Conectar Spotify**.
5. Agregar en el panel de Spotify las cuentas que participarán en la prueba.

La aplicación web usa OAuth con PKCE, por lo que no necesita ni debe guardar un
Client Secret en el navegador. El Client ID es configuración pública de la app y
no se solicita a los usuarios. La sesión de Spotify se guarda únicamente en
`sessionStorage` y desaparece al cerrar la sesión del navegador.

## Alcance de la demostración

- Las cuentas VOXMETRIKS pueden seguir siendo las que defina el proyecto.
- En Development Mode, Spotify permite actualmente hasta 5 cuentas autorizadas
  por aplicación. Esta restricción pertenece a Spotify, no al módulo de usuarios
  de VOXMETRIKS.
- La reproducción con Web Playback SDK requiere una cuenta Spotify Premium.
- Quien no conecte Spotify mantiene el catálogo, las recomendaciones y la
  analítica, pero debe conectarlo para reproducir música.
- La experiencia del producto es de audio y portada; no muestra controles ni
  superficies de video.

## Navegación asociada

- **Explorar** abre un panel lateral flotante, sin empujar el contenido.
- La barra superior muestra el espacio y módulo actuales.
- Los accesos directos cambian según el contexto: escucha personal, organización,
  datos o administración.
- La configuración de Spotify vive en **Música conectada**.
- La mezcla aparece en **Recomendaciones** y el reproductor conserva una sola
  fuente visible y autorizada: Spotify.
