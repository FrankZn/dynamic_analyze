# Add aop.py to env variable $PYTHONSTARTUP.

CURDIR=$(cd $(dirname ${BASH_SOURCE[0]}); pwd )
AOPPATH="${CURDIR}/src/aop.py"
export MY_STARTUP_FILE=${AOPPATH}
echo Add $AOPPATH to MY_STARTUP_FILE.
