#!/bin/bash

while true; do
    OPTION=$(whiptail --title "Main Menu" --menu "Choose an option:" 20 70 13 \
                    "1" "Update System and Install Prerequisites" \
                    "2" "Install Docker" \
                    "3" "Install and Setup Honeypot" \
                    "4" "Install Python to Capture Traffic" \
                    "5" "Configure Database Connection" \
                    "6" "Run the Capture" \
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
             echo "Installing Asterisk..."
             cd docker-asterisk
             sudo docker compose up -d --build
             ;;
        2)
             echo "Installing Kamailio..."
             ;;
        3)
             continue
             ;;
        *)
             echo "Invalid Option. Returning to Main Menu..."
             ;;

        esac
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
