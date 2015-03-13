'''
Created on Feb 8, 2015

@author: Rob
'''

from vgstation.common.plugin import IPlugin, Plugin
from vgstation.common.stringfixers import StringFixer as sf
import vgstation.common.config as globalConfig
import logging, random, re, time

@Plugin
class InfoBotPlugin(IPlugin):
    def __init__(self, bot):
        IPlugin.__init__(self, bot)
        
        self.data={
            'topics':{},
        }
        
        self.instructors=[]
        
        self.config=None
        
        self.tree = None
        self.nextTreeDownload=0
        
        self.config = globalConfig.get('plugins.infobot')
        if self.config is None:
            logging.warn('InfoBot: Disabled.') 
            return
        
        self.instructors=self.config.get('instructors',[])
        
        if len(self.instructors) == 0:
            self.config=None
            logging.error('InfoBot: No instructors defined, aborting load.')
            return
        
        self.LoadPluginData()
        
        self.RegisterCommand('forget', self.handle_forget, help='Tell me to forget a topic.')
        self.RegisterCommand('wrong,', self.handle_wrong, help='Tell me to correct a topic.')
        self.RegisterCommand('what', self.handle_what, help='Ask me about a topic.')
        self.RegisterCommand("what's", self.handle_what, help='Ask me about a topic.')
        self.RegisterCommand('add', self.handle_add, help='Add topic.')
        
        def q(pattern):
            return re.compile(pattern,flags=re.IGNORECASE)
        
        self.questionMarkers=[
            q('where is '),
            q('^whois '),   # Must match ^, else factoids with "whois" anywhere break
            q('^who is '),
            q('^what is (a|an)?'),
            q('^how do i '),
            q('^where can i (find|get|download)'),
            q('^how about '),
        ]
        
        # These are blatantly stolen from infobot. 
        # http://infobot.sf.net
        self.questionFixes=[     
            # clear the string of useless words.
            sf('^(stupid )?q(uestion)?:\s+',''),
            sf('^(does )?(any|ne)(1|one|body) know ',''),
            
            # fix the string.
            sf('^where is ',''),
            sf('\s+\?$','?'),
            sf('^whois ',''),   # Must match ^, else factoids with "whois" anywhere break
            sf('^who (is|was) ',''),
            sf('^what is (a|an)?',''),
            sf('^how do i (into )?',''),
            sf('^where can i (find|get|download)',''),
            sf('^how about ',''),
            sf(' da ',' the '),
    
            sf('^[uh]+m*[,\.]* +',''),
    
            sf('^well([, ]+)',''),
            sf('^still([, ]+)',''),
            sf('^(gee|boy|golly|gosh)([, ]+)',''),
            sf('^(well|and|but|or|yes)([, ]+)',''),
    
            sf('^o+[hk]+(a+y+)?([,. ]+)',''),
            sf('^g(eez|osh|olly)([,. ]+)',''),
            sf('^w(ow|hee|o+ho+)([,. ]+)',''),
            sf('^heya?,?( folks)?([,. ]+)',''),
        ]
        
    def handle_forget(self, event, args):
        channel = event.target
        nick = event.source.nick
        
        args=args[1:] # Nuke command itself.
        
        if nick not in self.instructors:
            self.bot.privmsg(channel, "You're not an instructor. Command ignored.")
            return
        
        if len(args) == 0:
            self.bot.privmsg(channel, 'Usage: bot, forget [about] <topic>')
            return
        
        if args[0].lower() == 'about':
            args=args[1:]
        
        if args[0].lower() == 'topic':
            args=args[1:]
        
        topic = args[0]
        if topic not in self.data['topics']:
            self.bot.privmsg(channel, 'Unknown topic {}'.format(topic))
            return
        
        del self.data['topics'][topic]
        self.SavePluginData()
        self.bot.privmsg(channel, 'Done.')
        if topic == self.topicContext: self.topicContext=None
        
    def handle_wrong(self, event, args):
        channel = event.target
        nick = event.source.nick
        
        args=args[1:] # Nuke command itself.
        
        if nick not in self.instructors:
            self.bot.privmsg(channel, "You're not an instructor. Command ignored.")
            return
        
        if len(args) == 0:
            self.bot.privmsg(channel, "Usage: bot, wrong, (it's|X is) [actually|really] <topic>")
            return
        
        # ntbot, wrong, it's actually hurf durf blarf
        # ntbot, wrong, X is actually harf blarf durf
        
        topic = None
        if args[1] == 'is':
            topic = args[0]
            if topic in ['it','that']:
                topic=None
            args=args[2:]
        if args[0] in ["it's", "that's"]:
            args=args[1:]
            
        if topic is None:
            topic=self.topicContext
        if topic is None:
            self.bot.privmsg(channel, "I have no clue what you're on about.");
            
        if topic not in self.data['topics']:
            self.bot.privmsg(channel, 'Unknown topic {}'.format(topic))
            return
        
        while args[0].lower() in ['really','actually']:
            args=args[1:]
        
        self.data['topics'][topic] = ' '.join(args)
        self.SavePluginData()
        self.bot.privmsg(channel, 'Done.')
        self.topicContext=topic
        
    def handle_what(self, event, args):
        channel = event.target
        nick = event.source.nick
        
        if len(args) == 0:
            self.bot.privmsg(channel, "Usage: bot, what [is] <topic>[?]")
            return

        args=args[1:] # Nuke command itself.
        
        while args[0].lower() in ['is','topic']:
            args=args[1:]
        
        topic = args[0]
        if topic.endswith('?'):
            topic=topic[:-1]
            
        if topic not in self.data['topics']:
            self.bot.privmsg(channel, 'Unknown topic {}'.format(topic))
            return
            
        self.blabTopic(channel, topic)
        
    def handle_add(self, event, args):
        channel = event.target
        nick = event.source.nick
        
        args=args[1:] # Nuke command itself.
        
        if args[0] != 'topic':
            return
        
        if nick not in self.instructors:
            self.bot.privmsg(channel, "You're not an instructor. Command ignored.")
            return
        
        if len(args) == 1:
            self.bot.privmsg(channel, "Usage: bot, add topic <topic> <message>")
            return

        while args[0].lower() in ['topic']:
            args=args[1:]
        
        topic = args[0]
            
        if topic in self.data['topics']:
            self.bot.privmsg(channel, 'Topic {} already exists.'.format(topic))
            return
        
        self.data['topics'][topic]=' '.join(args[1:])
        self.SavePluginData()
        self.bot.privmsg(channel, 'Done.')
        self.topicContext=topic
        
    def scanForQuestion(self, channel, question):
        if not question.endswith('?'):
            return
        question=question.lower()
        isQuestion=False
        for qMarker in self.questionMarkers:
            if qMarker.search(question) is not None:
                isQuestion=True
                break
        if not isQuestion: return
        
        for fix in self.questionFixes:
            question = fix.Fix(question)
        question = question[:-1] # strip ?
        chunks = question.split(' ')
        if chunks[0] in self.data['topics']:
            self.blabTopic(channel, chunks[0])
        
    def blabTopic(self, channel, topic):
        self.bot.privmsg(channel, self.data['topics'][topic])
        self.topicContext=topic
        
    def OnChannelMessage(self, connection, event):
        if self.config is None:
            return
        
        channel = event.target
        
        self.scanForQuestion(channel, event.arguments[0])
    