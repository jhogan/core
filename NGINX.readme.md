Nginx setup instructions
========================

Note that the following instructions were written for Ubuntu 20.04.

## Installation ##
Run the following commands

    sudo apt update
    sudo apt install nginx


## Firewall ##
On a default installation of Ubuntu, the ufw firewall will be 'inactive'
so there is no need for the purposes of this document to alter it. You
can check your system by running

    sudo ufw status

If you would like to administer the firewall a this point, these
documents will get you started:

* [How To Install Nginx on Ubuntu 20.04](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04)

* [Firewall – ufw status inactive on Ubuntu 22.04 Jammy Jellyfish Linux](https://linuxconfig.org/firewall-ufw-status-inactive-on-ubuntu-22-04-jammy-jellyfish-linux)

## Testing installation ##
At this point, there should be a basic Nginx server running on your
system serving a test page from port 80. You can test with a `curl`
request:

    curl  <my-ipaddress>

You can use `ifconfig` to get your server's public IP address.

## Managing Nginx ##
You can use `systemctl` to manage the Nginx service:

	# To stop your web server, type:
    sudo systemctl stop nginx

	# To start the web server when it is stopped, type:
    sudo systemctl start nginx

	# To stop and then start the service again, type:
    sudo systemctl restart nginx

    # If you are only making configuration changes, Nginx can often
    # reload without dropping connections. To do this, type:
    sudo systemctl reload nginx

    # By default, Nginx is configured to start automatically when the
    # server boots. If this is not what you want, you can disable this
    # behavior by typing:
    sudo systemctl disable nginx

    # To re-enable the service to start up at boot, you can type:
    sudo systemctl enable nginx


