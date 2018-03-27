from textblob import TextBlob
# from attributegetter import *
from generatengrams import ngrammatch
from Contexts import *
import json
from Intents import *
import random
import os
import re
import csv
import collections

def check_actions(current_intent, attributes, context):
    '''This function performs the action for the intent
    as mentioned in the intent config file'''
    '''Performs actions pertaining to current intent
    for action in current_intent.actions:
        if action.contexts_satisfied(active_contexts):
            return perform_action()
    '''
    #print(attributes)
    if(current_intent.action == "BookingRestaurantDone"):
        with open('Restauarant_Booking_output.csv', 'a') as f:
            w = csv.DictWriter(f, attributes.keys())
            w.writeheader()
            w.writerow(attributes)
    if(current_intent.action == "CabBookingDone"):
        with open('Cab_Booking_output.csv', 'a') as f:
            w = csv.DictWriter(f, attributes.keys())
            w.writeheader()
            w.writerow(attributes)

    print("If you are done with your booking, press Quit/exit to stop the process")
    context = IntentComplete()
    return 'action: ' + current_intent.action, context


def check_required_params(current_intent, attributes, context, user_input):
    '''Collects attributes pertaining to the current intent'''
    # print(current_intent)
    #if attributes is None:
    #print(attributes)

    headers = []
    for para in current_intent.params:
        # print(para.prompts)
        if para.required:
            if para.name not in attributes:
                #print(para.name)
                # if para.name=='RegNo':
                #   context = GetRegNo()
                # return random.choice(para.prompts), context
                if para.name == "08RestaurantConfirmation" and '05loczone' in attributes.keys() and '06cuisine' in attributes.keys() and '07Budget' in attributes.keys():
                    location = attributes['05loczone'].lower()
                    cuisine = attributes['06cuisine'].lower()
                    budget = attributes['07Budget'].lower()
                    #print(location)
                    rest_file = open("RestaurantDatabase.csv", "r")
                    rest_reader = csv.reader(rest_file)
                    for line in rest_reader:
                        #print(line[0],line[6])
                        if(line[0].lower()== location and line[1].lower()==cuisine and line[2].lower()==budget):
                            print(line[3])
                    #for line in rest_reader:
                     #   for i in range(5,line.):
                      #      if line[i][0] == location and line[i][1] == cuisine and line[i][2] == budget:
                       #         print(line[i][3])
                if para.name == '09cabPricing' or para.name == '11bookingConfirmation':
                    return random.choice(para.prompts), context
                else:
                    return (para.prompts[0]), context

    return None, context


def input_processor(user_input, context, attributes, intent):
    '''Spellcheck and entity extraction functions go here'''

    uinput = TextBlob(user_input).correct().string

    # update the attributes, abstract over the entities in user input
    attributes, cleaned_input = getattributes(user_input, context, attributes)

    return attributes, cleaned_input


def loadIntent(path, intent):
    with open(path) as fil:
        dat = json.load(fil)
        #u = dat.decode('utf-8-sig')
        #myObject = dat.encode('latin-1')
        intent = dat[intent]
        return Intent(intent['intentname'], intent['Parameters'], intent['actions'])

def conditionsImposed(attributes):

    for key,value in attributes.iteritems():
        if(key == '05customerPickup'):
            source = value
        if(key == '06customerDropoff'):
            destination = value
            if(source == destination):
                print("Source and destination cannot be the same..check again")
                del attributes[key]
                break

    return attributes

def intentIdentifier(clean_input, context, current_intent):
    #print(clean_input)
    clean_input = clean_input.lower()
    scores = ngrammatch(clean_input)
    scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])
    #print clean_input
    #print 'scores', scores
    #print("scores[-1][0] ",scores[-1][0])
    #print(scores[:-1])


    if (current_intent == None):
        # if(clean_input=="book"):
        #    return loadIntent('params/reqParams.cfg', 'BookACab')
        #if ('feedback' in clean_input ):
         #   return loadIntent('params/reqParams.cfg', 'Feedback')
        if("cab" in clean_input or 'ride' in clean_input):
            # return loadIntent('params/newparams.cfg','OrderBook')
            return loadIntent('params/reqParams.cfg', 'BookACab')
        if("restaurant" in clean_input or 'hotel' in clean_input or 'table' in clean_input):
            return loadIntent('params/reqParams.cfg','BookTableRestaurant')
        else:
            return loadIntent('params/reqParams.cfg', scores[-1][0])
    else:
        # print 'same intent'
        return current_intent

def validate(key,value):

    #validation for utilising cab services
    if(key == '01cabService' and value.isalpha()):
        if(value == 'no'):
            return False
        else:
            return True

    #validation for names
    if(key == '02passenger' or key == '05customerPickup' or key == '06customerDropoff' or key == '08lugguage'
       or key == '09cabPricing' or key == '11bookingConfirmation' or key =='14loczone' or key == '15cuisine' or key=='16Budget'):
        value = value.replace(' ','')
        if value.isalpha():
            return True
        else:
            print("Enter a valid name")
            return False

    if(key == '03customerNumber' or key == '10cabPayment'):
        if(re.search('^[6-9]\d{9}$',value) is not None):
            return True
        else:
            print("please check the number u have entered")
            return False

    if(key == '04customerMail'):
        if(len(value) > 7 and re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", value) != None):
            return True
        else:
            print("please check the input u have entered")
            return False

    if(key == '07numofPassengers'):
        if(value.isdigit()):
            val = int(value)
            if (val <= 4):
                print("We are booking Mini cab for you")
                cabType = "Mini cab"
                return True
            elif(val >= 5 and val <=6):
                print("We are booking Sedan for you")
                cabType = "Sedan"
                return True
            elif(val >= 7 and val <= 10):
                print("We are booking SUV for you")
                cabType = "SUV"
                return True
            else:
                print("Sorry...we didnot have such service available. Please check the input u have entered")
                cabType = None
                return False
        else:
            return False

    else:
        return True

def getattributes(uinput, context, attributes):
    '''This function marks the entities in user input, and updates
    the attributes dictionary'''
    # Can use context to to context specific attribute fetching
    current_attributes = {}
    if context.name.startswith('IntentComplete'):
        return attributes, uinput
    else:

        entities = {}
        for fil in files:
            #print(fil)
            lines = open(os.path.join('./entities/'+file_choosen+fil)).readlines()
            #print(lines)
            for i, line in enumerate(lines):
                # lines[i] = line[:-1]
                line = line.replace('\n', '')
                lines[i] = line
            entities[fil[:-4]] = '|'.join(lines)
        entities = collections.OrderedDict(sorted(entities.items()))
        #print(entities)

        # the are the given entities
        # {'title': 'Harry Potter|Laws of Physics|Harry Potter|Laws of Motion|Test|Test1|Language Learning',
        #  'storenames': 'Dominos|KFC|Pizza Hut|Subway|Airtel|Vodafone|Decathlon',
        # 'location': 'Delhi|Mumbai|Hyderabad|Chennai|Bangalore|Kolkata',
        # 'author': 'Issac Newton|Julia Michaels|Ben Frank|Noam Chomsky'}
        flag =0
        for entity in entities:
            # print(entity)
            for i in entities[entity].split('|'):
                if i.lower() == uinput.lower() and entity not in attributes:
                    # print(i.lower(), uinput.lower())
                    flag = 1
                    current_attributes[entity] = i
                    attributes[entity] = i
                    break

            if(flag == 1):
                break

            if(flag != 1 and (entity != '14loczone' or entity!='15cuisine' or entity!='16Budget' or entity!='17RestaurantConfirmation' or entity != '12TableBookingService')):
                if entity not in attributes and uinput not in StartTerms:
                    with open('./entities/' + entity + '.dat','a') as myFile:
                        myFile.write("\n"+uinput)
                    flag = 1
                    current_attributes[entity] = uinput
                    attributes[entity] = uinput


        for entity in entities:
            if '$' in uinput:
                uinput = re.sub(entities[entity], r'$' + entity, uinput, flags=re.IGNORECASE)

            # if context.name=='GetRegNo'  and context.active:
            #   match = re.search('[0-9]+', uinput)
            #  if match:
            #     uinput = re.sub('[0-9]+', '$regno', uinput)
            #    attributes['RegNo'] = match.group()
            #   context.active = False
        #print(current_attributes)
        #print(attributes)
        if len(current_attributes) > 0:
            for key, value in current_attributes.iteritems():
                result = validate(key,value)
                if(result):
                    #attributes = conditionsImposed(attributes)
                    return attributes, uinput
                else:
                    del attributes[key]
                    return attributes, uinput
        else:
            return attributes, uinput


class Session:
    def __init__(self, attributes=None, active_contexts=[FirstGreeting(), IntentComplete()]):

        '''Initialise a default session'''

        # Contexts are flags which control dialogue flow, see Contexts.py
        self.active_contexts = active_contexts
        self.context = FirstGreeting()

        # Intent tracks the current state of dialogue
        # self.current_intent = First_Greeting()
        self.current_intent = None

        # attributes hold the information collected over the conversation
        self.attributes = {}

    def update_contexts(self):
        '''Not used yet, but is intended to maintain active contexts'''
        for context in self.active_contexts:
            if context.active:
                context.decrease_lifespan()

    def reply(self, user_input):
        '''Generate response to user input'''
        # context=FirstGreeting(), attributes ={}, current_intent = None

        result = {}
        self.attributes, clean_input = input_processor(user_input, self.context, self.attributes, self.current_intent)

        #if(self.attributes is None):
        #    prompt = "please check the input u have entered"
        #    self.context.name = 'IntentComplete'
        #else:
        self.current_intent = intentIdentifier(clean_input, self.context, self.current_intent)
        prompt, self.context = check_required_params(self.current_intent, self.attributes, self.context,user_input)

        # prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name != 'IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)

        # Resets the state after the Intent is complete
        if self.context.name == 'IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None


        result["first_visitor"] = 0
        result["prompt"] = prompt
        return result


# starting point of the code
session = Session()


print 'HEXABOT: Hi, This is HexaBOT!, Do you want to book a cab or search a restaurant'

uinput = raw_input('User: ')
first_visitor = 0
attributes={}
if('01TableBookingService' not in attributes.keys() and '01cabService' not in attributes.keys()):

            first_visitor = 1
            dummy_input = uinput.lower()
            scores = ngrammatch(dummy_input)
            scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])
            # returns a list containing the names of the entries in the directory given by path
            if("cab" in uinput or "ride" in uinput):
                files = os.listdir('./entities/BookACab')
                file_choosen = 'BookACab/'
            elif("restaurant" in uinput or 'hotel' in uinput or 'table' in uinput):
                files = os.listdir('./entities/BookTableRestaurant')
                file_choosen = 'BookTableRestaurant/'
            else:
                files = os.path.join('./entities/',scores[-1][0])
                file_choosen = scores[-1][0]+'/'
            final_result = session.reply(uinput)
            print 'BOT:', final_result['prompt']
            first_visitor = final_result['first_visitor']

EndTerms = ["quit", "bye", "thank you", "thanks", "exit"]
StartTerms = ["hi", "hello"]
while True:
    if(first_visitor != 1):
        inp = raw_input('User: ')
        if (inp.lower() in EndTerms):
            print("Hope I served your purpose well. See you soon :)")
            break
        final_result = session.reply(inp)
        print 'BOT:',final_result['prompt']
        first_visitor = final_result['first_visitor']