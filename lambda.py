import logging
import requests
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
from ask_sdk_model.ui import Card

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PHR_NOT_CONNECTED = "Bonjour, vous devez être connecté à spotifaï pour utiliser cette skill. Pour cela, allez dans les paramètres de la skill dans votre application Alexa."
PHR_WELCOME = "Bonjour, je peux lister les appareils connectés ou lancer spotifaï sur un appareil. Que désirez-vous faire ?"
PHR_REPEAT = "Je n'ai pas compris votre demande. Que désirez-vous faire ?"
PHR_ERROR = "Désolé, une erreur s'est produite pendant l'exécution de votre demande. Pouvez-vous répéter ?"


class LaunchRequestHandler(AbstractRequestHandler):
    '''Handler for Skill Launch.'''

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type('LaunchRequest')(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info('HANDLER:LaunchRequest')

        # check account linking
        if handler_input.request_envelope.context.system.user.access_token is None:

            # give instructions for account linking
            return (
                handler_input.response_builder
                    .speak(PHR_NOT_CONNECTED)
                    .set_card(Card('LinkAccount'))
                    .response
            )

        else:

            # give features
            return (
                handler_input.response_builder
                    .speak(PHR_WELCOME)
                    .ask(PHR_REPEAT)
                    .response
            )


class ListDevicesIntentHandler(AbstractRequestHandler):
    '''Handler for ListDevices Intent.'''

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name('ListDevices')(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info('HANDLER:ListDevices')

        # check account linking
        if handler_input.request_envelope.context.system.user.access_token is None:

            # give instructions for account linking
            return (
                handler_input.response_builder
                    .speak(PHR_NOT_CONNECTED)
                    .set_card(Card('LinkAccount'))
                    .response
            )

        else:

            # retrieve devices
            devices = get_devices_list(handler_input.request_envelope.context.system.user.access_token)
            handler_input.attributes_manager.session_attributes = devices

            # build response
            deviceList = ''
            for i in devices:
                deviceList += '{}, {}. '.format(i, devices[i]['name'])
            logger.info('DEVICES_LIST:'.format(deviceList))
            speak_output = "J'ai trouvé ces appareils connectés : {} Sur lequel voulez-vous écouter spotifaï ?".format(deviceList)
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )


class PlayOnDeviceIntentHandler(AbstractRequestHandler):
    '''Handler for ListDevices Intent.'''

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name('PlayOnDevice')(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info('HANDLER:PlayOnDevice')

        # check account linking
        if handler_input.request_envelope.context.system.user.access_token is None:

            # give instructions for account linking
            return (
                handler_input.response_builder
                    .speak(PHR_NOT_CONNECTED)
                    .set_card(Card('LinkAccount'))
                    .response
            )

        else:

            # define user token
            user_token = handler_input.request_envelope.context.system.user.access_token

            # retrieve devices
            devices = handler_input.attributes_manager.session_attributes
            if not devices:
                devices = get_devices_list(user_token)

            # retrieve parameters
            slots = handler_input.request_envelope.request.intent.slots
            if 'deviceId' in slots and slots['deviceId'].value is not None:

                # play on with device id
                device_id = str(slots['deviceId'].value)
                logger.info('DEVICE_ID:{}'.format(device_id))
                if device_id in devices:
                    device_name = devices[device_id]['name']
                    if play_on(user_token, devices[device_id]['id']):
                        speak_output = "Lecture de spotifaï sur {}".format(device_name)
                    else:
                        speak_output = "Je ne suis pas parvenue à lancer spotifaï sur {}. Merci d'essayer ultérieurement.".format(device_name)
                else:
                    speak_output = "Je n'ai pas trouvé d'appareil avec ce numéro. Peut-être devriez-vous demander à connek tifaï la liste des appareils."

            elif "deviceName" in slots and slots['deviceName'].value is not None:

                # play on with device name
                device_name = str(slots['deviceName'].value).lower()
                logger.info('DEVICE_NAME:{}'.format(device_name))
                device_id = None
                for i in devices:
                    if device_name == devices[i]['name'].lower():
                        device_id = i
                if device_id is None:
                    speak_output = "Je n'ai pas trouvé d'appareil {}. Peut-être devriez-vous vérifier le nom de vos appareils avec la liste des appareils connectés.".format(device_name)
                else:
                    if play_on(user_token, devices[device_id]['id']):
                        speak_output = "Lecture de spotifaï sur {}".format(device_name)
                    else:
                        speak_output = "Je ne suis pas parvenue à lancer spotifaï sur {}. Merci d'essayer ultérieurement.".format(device_name)

            else:

                # default slots
                if 'deviceId' in slots:
                    logger.error('DEVICE_ID:{}'.format(str(slots['deviceId'].value)))
                if 'deviceName' in slots:
                    logger.error('DEVICE_NAME:{}'.format(str(slots['deviceName'].value).lower()))
                speak_output = "Je n'ai pas trouvé d'appareil correspondant. Peut-être devriez-vous demander à connek tifaï la liste des appareils."

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )


class HelpIntentHandler(AbstractRequestHandler):
    '''Handler for Help Intent.'''

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name('AMAZON.HelpIntent')(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # give features
        return (
            handler_input.response_builder
                .speak(PHR_WELCOME)
                .ask(PHR_REPEAT)
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    '''Generic error handling to capture any syntax or routing errors.'''

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool

        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response

        logger.error(exception, exc_info=True)
        return (
            handler_input.response_builder
                .speak(PHR_ERROR)
                .ask(PHR_ERROR)
                .response
        )


def get_devices_list(token):
    '''Retrieve connected devices from Spotify'''

    # type: (Token) -> dict

    response = requests.get(
        url = 'https://api.spotify.com/v1/me/player/devices',
        headers = {
            'Authorization': 'Bearer ' + token
        }
    )
    if response.status_code == 200:
        js = response.json()
        devices = {}
        n = 0
        for o in js['devices']:
            device = {
                'id': o['id'],
                'name': o['name']
            }
            logger.info('DEVICE:{}'.format(device))
            n += 1
            devices[str(n)] = device
        return devices
    else:
        logger.error('HTTP_CODE:{}'.format(response.status_code))
        logger.error('HTTP_RESPONSE:{}'.format(response.text))
        return {}


def play_on(token, deviceId):
    '''Transfer playback to an other Spotify device'''

    # type: (Token, DeviceID) -> bool

    logger.info('DEVICE_ID:{}'.format(deviceId))
    response = requests.put(
        url = 'https://api.spotify.com/v1/me/player',
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        },
        json = {
            'device_ids': [deviceId],
            'play': True
        }
    )
    if response.status_code >= 200 and response.status_code < 250:
        return True
    else:
        logger.error('HTTP_CODE:{}'.format(response.status_code))
        logger.error('HTTP_RESPONSE:{}'.format(response.text))
        return False



# define SkillBuilder

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ListDevicesIntentHandler())
sb.add_request_handler(PlayOnDeviceIntentHandler())
sb.add_request_handler(HelpIntentHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
