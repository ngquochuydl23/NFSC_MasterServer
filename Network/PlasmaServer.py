from twisted.internet.protocol import Protocol

from DataClasses import Server
from Framework.Server.Plasma import *
from Globals import Servers
from Logger import Log
from Utilities.Packet import Packet


class HANDLER(Protocol):
    def __init__(self):
        self.CONNOBJ = None
        self.logger = Log("PlasmaServer", "\033[36;1m")
        self.logger_err = Log("PlasmaServer", "\033[36;1;41m")

    def connectionMade(self):
        self.ip, self.port = self.transport.client
        self.transport.setTcpNoDelay(True)

        self.logger.new_message("[" + self.ip + ":" + str(self.port) + "] connected", 1)

        if self.CONNOBJ is None:
            self.CONNOBJ = Server()
            self.CONNOBJ.ipAddr = self.ip
            self.CONNOBJ.networkInt = self.transport
            self.CONNOBJ.GameID = len(Servers) + 1
            Servers.append(self.CONNOBJ)

    def connectionLost(self, reason):
        self.logger.new_message("[" + self.ip + ":" + str(self.port) + "] disconnected ", 1)

        if self.CONNOBJ is not None:
            self.CONNOBJ.IsUp = False
            Servers.remove(self.CONNOBJ)

        return

    def dataReceived(self, data):
        packet_type = data[:4]
        packet_checksum = data.split(packet_type)[1].split("TXN")[0]
        packet_id = Packet(None).getPacketID(packet_checksum[:4])
        packet_length = packet_checksum[4:]
        packet_data = data.split(packet_type + packet_checksum)[1]

        self.logger.new_message("[" + self.ip + ":" + str(self.port) + "]<-- " + repr(data), 3)

        dataObj = Packet(packet_data).dataInterpreter()

        if packet_id == 0x80000000:  # Don't count it
            pass
        else:
            self.CONNOBJ.plasmaPacketID += 1

        if Packet(data).verifyPacketLength(packet_length):
            TXN = dataObj.get("PacketData", "TXN")

            if packet_type == "fsys":
                fsys.ReceivePacket(self, dataObj, TXN)
            elif packet_type == 'acct':
                acct.ReceivePacket(self, dataObj, TXN)
            elif packet_type == 'asso':
                asso.ReceivePacket(self, dataObj, TXN)
            else:
                self.logger_err.new_message(
                    "[" + self.ip + ":" + str(self.port) + ']<-- Got unknown message type (' + packet_type + ")", 2)
        else:
            self.logger_err.new_message("Warning: Packet Length is diffirent than the received data length!"
                                        "(" + self.ip + ":" + self.port + "). Ignoring that packet...", 2)