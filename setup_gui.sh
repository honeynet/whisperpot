#!/bin/bash

while true; do
    OPTION=$(whiptail --title "Main Menu" --menu "Choose an option:" 20 70 13 \
                    "1" "Update System and Install Prerequisites" \
                    "2" "Install Docker" \
                    "3" "Install and Setup Honeypot" \
                    "4" "Install Python to Capture Traffic" \
                    "5" "Configure Database Connection" \
                    "6" "Run the SIP Capture" \
                    "7" "Install ELK" \
                    "8" "Install Grafana" \
                    "10" "Show Status" 3>&1 1>&2 2>&3)
    # Script version 1.0 updated 24 May 2023
    # Depending on the chosen option, execute the corresponding command
    case $OPTION in
    1)
        sudo apt-get update -y
        sudo apt-get upgrade -y
        sudo apt-get install wget curl nano git -y
        ;;
    2)
        # Check if Docker is installed
        if command -v docker > /dev/null; then
            echo "Docker is already installed."
        else
            # Install Docker
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo systemctl enable docker.service && sudo systemctl enable containerd.service
        fi
        ;;
    3)
        HONEYPOT_OPTION=$(whiptail --title "Honeypot Setup" --menu "Choose a honeypot:" 20 70 10 \
                                 "1" "Asterisk" \
                                 "2" "Kamailio" \
                                 "3" "Go back to Main Menu" 3>&1 1>&2 2>&3)

        case $HONEYPOT_OPTION in
        1)
         ASTERISK_OPTION=$(whiptail --title "Asterisk Setup" --menu "Choose an Asterisk option:" 20 70 10 \
                                 "1" "Asterisk Standalone (Capture SIP only)" \
                                 "2" "Asterisk with Web-based GUI (Capture SIP and HTTP)" 3>&1 1>&2 2>&3)
         case $ASTERISK_OPTION in
          1)
            echo "Installing Asterisk Standalone..."
            cd docker-asterisk/asterisk-standalone
            sudo docker compose up -d --build
            sudo docker exec asterisk-standalone-asterisk-1 /usr/sbin/asterisk
            ;;
          2)
            echo "Installing Asterisk with Web-based GUI..."
            cd docker-asterisk/asterisk-standalone
            sudo docker compose up -d --build
            sudo docker exec asterisk-gui-asterisk-1 /usr/sbin/asterisk
            cd ../docker-http-honeypot
            sudo docker compose up -d --build
            ;;
          *)
            echo "Invalid Option. Returning to Asterisk Menu..."
            ;;
    esac
    ;;
        2)
         KAMAILIO_OPTION=$(whiptail --title "Kamailio Setup" --menu "Choose a Kamailio option:" 20 70 10 \
                                 "1" "Kamailio Standalone (Capture SIP only)" \
                                 "2" "Kamailio with Web-based GUI (Capture SIP and HTTP)" 3>&1 1>&2 2>&3)
         case $KAMAILIO_OPTION in
          1)
            echo "Installing Kamailio Standalone..."
            cd docker-kamailio/kamailio-standalone
            sudo docker compose up -d --build
            ;;
          2)
            echo "Installing Kamailio with Web-based GUI..."
            cd docker-kamailio/kamailio-standalone
            sudo docker compose up -d --build
            cd ../docker-http-honeypot
            sudo docker compose up -d --build
            ;;
          *)
            echo "Invalid Option. Returning to Kamailio Menu..."
            ;;
    esac
    ;;
        3)
             continue
             ;;
        *)
             echo "Invalid Option. Returning to Main Menu..."
             ;;

        esac
        ;;
    4)
        cd docker-jupyter
        sudo docker compose up -d --build
        echo "Installation done"
        ;;
    5)
        # Prompt the user for the DB_HOST
        DB_HOST=$(whiptail --inputbox "Enter the database host:" 8 40 3>&1 1>&2 2>&3)
        # Prompt the user for the DB_USER
        DB_USER=$(whiptail --inputbox "Enter the database user:" 8 40 3>&1 1>&2 2>&3)
        # Prompt the user for the DB_PASSWORD
        DB_PASSWORD=$(whiptail --passwordbox "Enter the database password:" 8 40 3>&1 1>&2 2>&3)
        # Prompt the user for the DB_NAME
        DB_NAME=$(whiptail --inputbox "Enter the database name:" 8 40 3>&1 1>&2 2>&3)
        # Create the .env file
        echo "DB_HOST=$DB_HOST" > ./docker-jupyter/app/.env
        echo "DB_USER=$DB_USER" >> ./docker-jupyter/app/.env
        echo "DB_PASSWORD=$DB_PASSWORD" >> ./docker-jupyter/app/.env
        echo "DB_NAME=$DB_NAME" >> ./docker-jupyter/app/.env

        echo "DB_HOST=$DB_HOST" > ./docker-http-honeypot/.env
        echo "DB_USER=$DB_USER" >> ./docker-http-honeypot/.env
        echo "DB_PASSWORD=$DB_PASSWORD" >> ./docker-http-honeypot/.env
        echo "DB_NAME=$DB_NAME" >> ./docker-http-honeypot/.env
        # Print a message to indicate that the .env file has been created
        whiptail --msgbox ".env file has been created" 8 40
        ;;
    6)
        sudo docker exec docker-jupyter-jupyter-1 nohup python ./work/sip_capture.py > /dev/null 2>&1 &
        ;;
    10)
        sudo docker ps;
        ;;
esac
    # Give option to go back to the previous menu or exit
    if (whiptail --title "Exit" --yesno "Do you want to exit the script?" 8 78); then
        break
    else
        continue
    fi
done
