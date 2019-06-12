import logging
import time

from .bus import Bus
from .network import Network
from .client import Client

class Bridge():
    """
    Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection(s) together.
    """

    def __init__(self, settings):
        """
        Initialises the Bridge class.
        """

        # Logger
        self.__logger = logging.getLogger("VelbusTCP")

        self.__settings = settings

        # Create bus
        self.__bus = Bus(options=settings["serial"], bridge=self)

        # Create network connection(s)
        self.__networks = []
        for connection in settings["connections"]:
            self.__networks.append(Network(options=connection, bridge=self))
        
    def start(self):
        """
        Starts bus and when succesful, starts TCP network(s).
        """

        while not self.__bus.is_active():

            try:
                self.__bus.start()
            except:
                self.__logger.error("Couldn't create bus connection, waiting 5 seconds")
                time.sleep(5)

        for network in self.__networks:
            network.start()

    def bus_error(self):
        """
        Called when bus goes into error.

        Closed both bus, then re-opens.
        """

        self.__bus.stop()
        self.start()
    
    def bus_packet_received(self, packet):
        """
        Called when the serial connection receives a packet.

        :param packet: The received packet on the serial connection.
        """

        assert isinstance(packet, bytearray)

        self.__logger.debug("[BUS IN] " + " ".join(hex(x) for x in packet))

        for network in self.__networks:
            if network.is_active():
                network.send(packet)

    def tcp_packet_received(self, network, client, packet):
        """
        Called when a network receives a packet from a client.

        :param network: Network which received the packet
        :param client: Client which sent the packet
        :param packet: Packet received from the client
        """

        assert isinstance(network, Network)
        assert isinstance(client, Client)
        assert isinstance(packet, bytearray)

        #TODO: Only send to network if bus is active?

        self.__logger.debug("[TCP IN] " + " ".join(hex(x) for x in packet))

        for n in self.__networks:

            if n.is_active():

                # Relay to other TCP clients?
                if (network == n) and not network.relay():
                    continue
            
                network.send_exclude(packet, client)

        if self.__bus.is_active():
            self.__bus.send(packet)        

    def stop(self):
        """
        Stops bus and network.
        """

        self.__bus.stop()

        for network in self.__networks:
            network.stop()