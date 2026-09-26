#!/usr/bin/env python3

import logging

from ctf_gameserver import checkerlib

import utils
import random
import pwn
import json

from utils import CrewDescriptor, MessageHeader, BeingDescriptor, IdentityHeader, fetch, generate_unique_uname, get_being

from typing import cast

pwn.context.log_level = 'debug'
pwn.context.timeout = 15

PORT: str = "8080"

class IMChecker(checkerlib.BaseChecker):

    def place_flag(self, tick):
        logging.info("Placing flag 1")
        flag = checkerlib.get_flag(tick, 0)

        p: pwn.connect | None
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN
        (idh, bdr) = utils.create_being(p = p, name = generate_unique_uname(), crew_id = None)
        logging.info("got identity header: %s", str(idh))
        logging.info("got being descriptor: %s", str(bdr))
        if not idh or not bdr:
            logging.info("create being did not return a identity header and being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        p.close()
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN

        (idh2, cdr) = utils.create_crew(p = p, crew_name= generate_unique_uname(), idh = idh, captain =  idh.id, equipment = [flag], invited = [])
        if not idh or not cdr:
            logging.info("create being did not return a identity header and being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        checkerlib.store_state(str(tick)+"_0", {"flag": flag, "idh": json.dumps(idh._asdict())})
        checkerlib.set_flagid(str(cdr.id), 0)
        p.close()

        logging.info("Placing flag 2")
        flag = checkerlib.get_flag(tick, 1)
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            return checkerlib.CheckResult.DOWN

        (idh, bdr) = utils.create_being(p = p, name= generate_unique_uname(), crew_id = None)
        if not idh or not bdr:
            logging.info("create being did not return a identity header and being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        logging.info("got identity header: %s", str(idh))
        logging.info("got being descriptor: %s", str(bdr))
        p.close()
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN

        sdr = utils.create_spaceship(p = p, s_name=  generate_unique_uname(),idh = idh, crew = None, resources = [flag],janitor = bdr.id);
        if not sdr:
            logging.info("create being did not return a identity header and being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        checkerlib.store_state(str(tick)+"_1", {"flag": flag, "idh": json.dumps(idh._asdict())})
        checkerlib.set_flagid(str(sdr.id), 1)

        return checkerlib.CheckResult.OK


    def check_service(self):
        # TODO: Implement (maybe use `utils.generate_message()`)
        # Test reate being
        p: pwn.connect | None
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            return checkerlib.CheckResult.DOWN

        logging.info("creating being")
        logging.info("#########################################")
        (idh_captain, bdr_captain) = utils.create_being(p = p, name= generate_unique_uname(), crew_id = None)
        if not idh_captain or not bdr_captain:
            logging.info("create being did not return a identity header and being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY

        (idh_captain, bdr_captain) = utils.get_being(p, idh_captain.id, idh_captain.name, idh_captain.auth)
        if not idh_captain or not bdr_captain:
            logging.info("could not fetch the created being")
            p.close()
            return checkerlib.CheckResult.FAULTY
        
        logging.info("testing create being")
        logging.info("#########################################")
        logging.info("test negative values returns error")
        logging.info("------------------")
        utils.send_msg_header(p, MessageHeader(2, "CREATE", 2, "BEING", "REQUEST", []))
        utils.send_identity_header(p, IdentityHeader("", idh_captain.name, ""))
        utils.send_being_descriptor(p, BeingDescriptor(None, idh_captain.name, -1, -1, "", -1, None, None))
        resp = p.recvline().rstrip()
        msh = utils.parse_msh(resp)
        if msh == None:
            logging.info("got no response message header")
            logging.info("got %s instead", str(resp))
            p.close()
            return checkerlib.CheckResult.FAULTY
        resp = p.recvline().rstrip()
        if b"RVJS" not in resp:
            logging.info("did not get an error header")
            logging.info("got %s instead", str(resp))
            p.close()
            return checkerlib.CheckResult.FAULTY
        
        logging.info("test sending auth in create returns error")
        logging.info("------------------")
        utils.send_msg_header(p, MessageHeader(2, "CREATE", 2, "BEING", "REQUEST", []))
        utils.send_identity_header(p, IdentityHeader("", idh_captain.name, "non_empty_auth"))
        utils.send_being_descriptor(p, BeingDescriptor(None, idh_captain.name, -1, -1, "", -1, None, None))
        resp = p.recvline().rstrip()
        msh = utils.parse_msh(resp)
        if msh == None:
            logging.info("got no response message header")
            logging.info("got %s instead", str(resp))
            p.close()
            return checkerlib.CheckResult.FAULTY
        if b"RVJS" not in p.recvline().rstrip():
            logging.info("did not get an error header")
            logging.info("got %s instead", str(resp))
            p.close()
            return checkerlib.CheckResult.FAULTY

        logging.info("create crew")
        logging.info("#########################################")
        # create crew
        # close cuz bug
        p.close()
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN

        (tmp, cdr) = utils.create_crew(p, crew_name= generate_unique_uname(), idh = idh_captain, captain = idh_captain.id)

        if not tmp or not cdr:
            p.close()
            return checkerlib.CheckResult.FAULTY

        logging.info("create mission")
        logging.info("#########################################")
        (tmp, mdr) = utils.create_mission(p, name= generate_unique_uname(), idh = idh_captain)
        if not tmp or not mdr:
            logging.info("create mission did not return a identity header and mission descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY

        logging.info("testing create crew")
        logging.info("#########################################")
        logging.info("------------------")
        # TODO
        # close cuz bug
        p.close()
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN


        logging.info("create spaceship")
        logging.info("#########################################")

        sdr = utils.create_spaceship(p, s_name= generate_unique_uname(), idh = idh_captain,crew = cdr.id)
        if not sdr:
            logging.info("create mission did not return a identity header and mission descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY

        logging.info("testing spaceship being")
        logging.info("#########################################")
        # TODO creating spaceship for crew you are not captain/part of fails
        # no crew
        tmp = utils.create_spaceship(p, s_name= generate_unique_uname(), idh = idh_captain)

        if not tmp:
            return checkerlib.CheckResult.FAULTY

        logging.info("update")
        logging.info("#########################################")

        old_bdr_captain = bdr_captain
        bdr_captain: BeingDescriptor | None = bdr_captain
        bdr_captain = BeingDescriptor(bdr_captain.id, "", "", 0xdead, "", "", "", "")
        tmp = utils.update_being(p, idh_captain, bdr_captain)
        if not tmp:
            logging.info("update being did not return a identity header and mission descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        if old_bdr_captain.remaining_lives == tmp.remaining_lives:
            logging.info("the remaining lives stayed the same")
            return checkerlib.CheckResult.FAULTY
        old_bdr_captain = tmp
        bdr_captain = BeingDescriptor(bdr_captain.id, "", 0x67, "", "bals6742", "", "", "^3^^adfs^")
        tmp = utils.update_being(p, idh_captain, bdr_captain)
        if not tmp:
            logging.info("update being did not return a identity header and mission descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY
        if tmp.age == old_bdr_captain.age or tmp.skills == old_bdr_captain.skills or tmp.diseases != old_bdr_captain.diseases:
            logging.info("the skills stayed the same or the age changed")
            logging.info("should be %s was %s", old_bdr_captain, tmp)
            return checkerlib.CheckResult.FAULTY
        old_bdr_captain = tmp

        logging.info("joni crew")
        logging.info("#########################################")

        (idh_crew, bdr_crew) = utils.create_being(p, generate_unique_uname())
        if not bdr_crew or not idh_crew:
            logging.info("create being did not return a identity header and mission descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY

        cdr = CrewDescriptor(cdr.id, "", "", "", "", cdr.invited + "^" + str(bdr_crew.id) + "^")
        cdr = utils.update_crew(p, idh_captain, cdr)
        if not cdr:
            logging.info("update crew did not return a crew descriptor")
            return checkerlib.CheckResult.FAULTY
        cdr = cdr

        bdr_crew = BeingDescriptor(bdr_crew.id, "", "", "", "", cdr.id, "", "")
        bdr_crew = utils.update_being(p, idh_crew, bdr_crew)
        if not bdr_crew:
            logging.info("update being did not return a being descriptor")
            p.close()
            return checkerlib.CheckResult.FAULTY

        (tmp2, tmp) = get_being(p, idh_crew.id, idh_crew.name, idh_crew.auth)
        if not tmp:
            return checkerlib.CheckResult.FAULTY
        if tmp.crew_id != cdr.id:
            return checkerlib.CheckResult.FAULTY
        (tmp2, tmp) = utils.fetch_crew(p, idh_crew, cdr.id)
        if not tmp:
            return checkerlib.CheckResult.FAULTY
        if tmp[0].id != cdr.id:
            return checkerlib.CheckResult.FAULTY
        if idh_crew.id in tmp[0].invited:
            logging.error("crew id still in invited of joined crew")
            return checkerlib.CheckResult.FAULTY

        return checkerlib.CheckResult.OK


    def check_flag(self, tick):
        logging.info("Checking flag 1")
        p: pwn.connect | None
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN

        state = checkerlib.load_state(str(tick)+"_0")
        if not state:
            logging.error(f"Unable to load state for flag 2 in tick {tick}")
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        flag = state["flag"]
        idh = json.loads(state["idh"])
        (idh, crews) = utils.fetch_crew(p, IdentityHeader(idh["id"], idh["name"], idh["auth"]), captain=idh["id"])
        if not idh or not crews:
            logging.error("fetch crew failed")
            p.close()
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        for crew in crews:
            if flag in crew.equipment.decode():
                break
        else:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        logging.info("Flag 1 checked successfully")
        p.close()

        logging.info("Checking flag 2")
        p = utils.connection_or_fail(self.ip, PORT)
        if not p:
            return checkerlib.CheckResult.DOWN
        if len(p.recvuntil(b"Welcome to Interstellar Mission Controll v67\n")) <= 0:
            logging.error("Didn't recv 67!")
            return checkerlib.CheckResult.DOWN

        state = checkerlib.load_state(str(tick)+"_1")
        if not state:
            logging.error(f"Unable to load state for flag 2 in tick {tick}")
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        flag = state["flag"]
        idh = json.loads(state["idh"])
        (idh, spaceships) = utils.fetch_spaceship(p, IdentityHeader(idh["id"], idh["name"], idh["auth"]))
        if not idh or not spaceships:
            logging.error("fetch spaceships failed")
            p.close()
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        for spaceship in spaceships:
            if flag in spaceship.resources:
                break
        else:
            logging.error("Couldnt find flag: %s", flag)
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        logging.info("Flag 2 checked successfully")
        return checkerlib.CheckResult.OK
        p.close()


if __name__ == '__main__':

    checkerlib.run_check(IMChecker)
