# Generate alt texts

First clone the repository and install the dependencies on a (virtual) machine with access to a GPU:

```sh
apt update
apt install python3-pip

git clone https://github.com/kangasta/photo-objects.git
cd photo-objects/

pip3 install --break-system-packages -r generate/requirements.txt
```

Configure the Photo Objects access by setting `PHOTO_OBJECTS_URL`, `PHOTO_OBJECTS_USERNAME`, and `PHOTO_OBJECTS_PASSWORD` environment variables.

Generate alt texts for images that do not yet have alt text or a pending change request to add one:

```sh
python3 generate/alt_texts.py 0
```
