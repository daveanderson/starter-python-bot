import os

from docker import Client
from distutils.dir_util import copy_tree

image_name = "electrobarn/ssh-openvpn:latest"

class Configurator(object):
    """
    Configurator performs file operations
    """
    def __init__(self, host_configuration_root, configuration_root):
        super(Configurator, self).__init__()
        self.host_config_root = host_configuration_root
        self.config_root = configuration_root
        self.cli = Client(base_url='unix://var/run/docker.sock')
        if not os.path.isdir(self.config_root):
            print "Error: the configuration folder `" + self.config_root + "` does not exist."
            return
        
        # make sure we have the latest ssh to vpn bridge image
        self.cli.pull(image_name)
        # images = cli.images(name=image_name)
        

    def create_configuration(self, user, channel, msg_writer):
        """create_configuration will create the base"""
        
        (success, target_dir, host_target_dir) = self._check_configuration(user, channel, msg_writer)
        if success:
            return
        # create the folder for this user
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        base_dir = os.path.join(self.config_root, "base")        
        if not os.path.exists(base_dir):
            msg_writer.send_message(channel, "Sorry, I'm missing the folder `base` that contains the base for each tunnel configuration. I can't create a tunnel for you. Please contact a human to investigate.")
            return
        copy_tree(base_dir, target_dir)
        msg_writer.send_message(channel, "Ok, your base configuration exists. Please contact a human to put your `id_rsa.pub` and VPN credentials (`vpn.auth`) in place.")
        

    def start_container(self, user, channel, msg_writer):
        """start_container starts a container for the user"""
        
        (success, target_dir, host_target_dir) = self._check_configuration(user, channel, msg_writer)
        if not success:
            return "Failed to start tunnel."
        
        containers = self.cli.containers(all=True, filters={"name": user})
        action = ""
        if len(containers) == 0:
            msg_writer.send_message(channel, "Okay, I don't already have a tunnel for " + user + ", so I'll create one!")
            host_config = self.cli.create_host_config(cap_add=["NET_ADMIN"], devices=["/dev/net/tun"], port_bindings={22: 30022}, binds={host_target_dir: {"bind": "/vpn", "mode": "rw"}})
            container = self.cli.create_container(image=image_name, detach=True, volumes=["/vpn"], name=user, ports=[22], host_config=host_config)
            response = self.cli.start(container=container.get('Id'))
            container = self.cli.containers(all=True, filters={"name": user})[0]
            action = "Started"
        else:
            msg_writer.send_message(channel, "Because I already have a tunnel for " + user + ", I'll just restart it.")
            container = containers[0]
            msg_writer.send_message(channel, "Restarting tunnel for " + user + ".")
            self.cli.restart(container)
            container = self.cli.containers(all=True, filters={"name": user})[0]
            action = "Restarted"
        status = container.get("Status")
        ports = container.get("Ports")[0]
        port = str(ports.get("PublicPort"))
        return action + " tunnel.\n> Port: " + port + "\n> Status: " + status + "\nPlease let me know when I should `stop` this tunnel."
    
    def stop_container(self, user, channel, msg_writer):
        """stop_container stops a container for the user"""
        
        (success, target_dir, host_target_dir) = self._check_configuration(user, channel, msg_writer)
        if not success:
            return
        
        containers = self.cli.containers(all=True, filters={"name": user})
        if len(containers) == 0:
            msg_writer.send_message(channel, "Shucks, I don't have a tunnel for " + user + ". Here I am with nothing to do.")
        else:
            container = containers[0]
            status = container.get("Status")
            if "137" in status:
                msg_writer.send_message(channel, "It looks like the tunnel for " + user + " was previously stopped.\nLet me know if you need me to `start` it again.")
                return
            msg_writer.send_message(channel, "Okey doke, I'll stop the tunnel for " + user + ".\nHang on, I'll let you know when I'm done.")
            self.cli.stop(container)
            msg_writer.send_message(channel, "Done! The tunnel for " + user + " is now stopped.\nMake sure you tell me if I should `start` it again.")

    def container_status(self, user, channel, msg_writer):
        """docstring for container_status"""
        (success, target_dir, host_target_dir) = self._check_configuration(user, channel, msg_writer)
        if not success:
            return
        self._status(user, channel, msg_writer)

    def _check_configuration(self, user, channel, msg_writer):
        """_check_configuration checks if we have a container for this user"""
        
        target_dir = os.path.join(self.config_root, user)
        host_target_dir = os.path.join(self.host_config_root, user)
        if os.path.isdir(target_dir):
            msg_writer.send_message(channel, "Sweet, I have the configuration directory for " + user + ".")
            return (True, target_dir, host_target_dir)
        else:
            msg_writer.send_message(channel, "Sorry, I'm missing the configuration folder for " + user + ".\nIf you have VPN credentials, you can tell me to `create` and I'll create most of your configuration. A human you trust will have to put the secure bits (`id_rsa.pub` and VPN credentials) in place...")
            return (False, target_dir, host_target_dir)
    
    def _status(self, user, channel, msg_writer):
        """looks up and outputs the status of the container for the user"""
        containers = self.cli.containers(all=True, filters={"name": user})
        if len(containers) == 0:
            msg_writer.send_message(channel, "Sorry, I don't have an active tunnel for " + user + ".\nNo status to report.")
        else:
            container = containers[0]
            status = container.get("Status")
            ports = container.get("Ports")
            port = "n/a"
            if len(ports) > 0:
                port = str(ports[0].get("PublicPort"))
            msg_writer.send_message(channel, "Tunnel for " + user + ".\n> Port: " + port + "\n> Status: " + status)
