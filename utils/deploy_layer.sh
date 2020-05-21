# !bin/bash
function usage(){
    printf '\t-l\t--library\tPip library\n'
    printf '\t-v\t--version\tVersion of the package\n'
    printf '\t-u\t--usage\t\tShow Help'
}

# Parse args
POSITIONAL=()
while [[ $# -gt 0 ]]
do key="$1"

case $key in 
    -l|--library)
        LIBRARY="$2"
        shift
        shift
        ;;
    -v|--version)
        VERSION="$2"
        shift
        shift
        ;;
    -u|--usage)
        usage
        shift
        shift
        ;;
esac
done
set -- "${POSITIONAL[@]}"

echo $LIBRARY
echo $VERSION

# Install library on a docker and keep the package
LAYER_NAME=$LIBRARY
echo $LIBRARY==$VERSION >> requirements.txt
docker run -v "$PWD":/var/task "lambci/lambda:build-python3.6" /bin/sh -c "pip3 install -r requirements.txt -t python/lib/python3.6/site-packages/; exit"
#find python/ -name "*.so" | xargs strip
zip -r $LIBRARY.zip python > /dev/null

FILESIZE=$(stat -c%s "$LIBRARY.zip")

printf "Filesize : $FILESIZE"


# If the package size is lower than 50 Mo : traditional lambda deployment
if [ $(((FILESIZE+0)/1000000)) -lt 50 ] ;
then
    aws lambda publish-layer-version --layer-name $LIBRARY --zip-file fileb://$LIBRARY.zip --compatible-runtimes "python3.6" --region "eu-west-3"

# If the package size is bigger than 50 Mo : the package is pushed on S3 and then deployed
else 
    BUCKET_NAME="datatext-pip"
    aws s3 cp $LIBRARY.zip s3://$BUCKET_NAME/$LIBRARY.zip
    aws lambda publish-version --layer-name $LIBRARY --content S3Bucket=$BUCKET_NAME,S3Key=$LIBRARY.zip --compatible-runtimes "python3.6" --region "eu-west-3"
fi

rm requirements.txt
rm -rf python
rm $LIBRARY.zip