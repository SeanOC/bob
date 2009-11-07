import sqlite3
import os
from optparse import OptionParser
from datetime import datetime
import time

import pysvn
from pinder import Campfire

import settings

class Bob(object):
    room = None
    campfire = None
    stdin_path = '/dev/null'
    stdout_path = settings.LOG_FILE
    stderr_path = settings.ERROR_FILE
    pidfile_path = settings.LOCK_FILE
    pidfile_timeout = settings.LOCK_TIMEOUT
    files_preserve = [settings.DB_FILE, ]
        
    def startup(self):
        self.campfire = Campfire(
            settings.CAMPFIRE_DOMAIN,
            ssl=settings.CAMPFIRE_SSL
        )
        self.campfire.login(settings.CAMPFIRE_LOGIN, settings.CAMPFIRE_PASSWORD)
        self.room = self.campfire.find_room_by_name(settings.CAMPFIRE_ROOM)
        self.room.join()
        self.room.speak("I'm alive!")

    # Main function
    def run(self):
        if self.is_reset_mode():
            self.reset_db()
        else:
            self.startup()
            self.db = self.get_db_cursor()
            while True:
                entry = self.get_next_entry()
                while entry:
                    self.room.ping()
                    if self.is_entry_interesting(entry):
                        self.report_entry(entry)
                    self.record_processed(entry)
                    entry = self.get_next_entry()
                time.sleep(30)
            
    def stop(self, *args, **kwargs):
        print args
        print kwargs
        self.room.speak("I'm going down!")
        self.room.leave()
        self.campfire.logout()
                    
    # Campfire Fuctions
    def report_entry(self, entry):
        msg = self.gen_message(entry)
        self.room.speak(msg)

    # SVN Functions
    def get_next_entry(self):
        last_rev = self.get_last_entry()
        if last_rev:
            next = last_rev + 1
            target_rev = pysvn.Revision(pysvn.opt_revision_kind.number, next)
        else:    
            target_rev = pysvn.Revision(pysvn.opt_revision_kind.head)

        try:
            client = pysvn.Client()
            entries = client.log(
                settings.SVN_SERVER,
                revision_start = target_rev,
                discover_changed_paths = True,
                limit = 1
            )
            entry = entries[0]
        except pysvn.ClientError:
            entry = None

        return entry

    def get_last_entry(self):
        query = "SELECT rev FROM svn_log ORDER BY processed DESC LIMIT 1"
        result = self.db.execute(query)
        rev = result.fetchone()
    
        if rev:
            rev = rev[0]
    
        return rev

    def is_entry_interesting(self, entry):
        interesting = False
        for change in entry.changed_paths:
            for prefix in settings.SVN_WATCH_PATHS:
                if change.path.startswith(prefix):
                    interesting = True
                    break

        return interesting
    
    def gen_message(self, entry):
        rev = entry.revision.number
        url = settings.COMMIT_URL % rev
        msg = '[%d] %s - "%s" (%s)' % (rev, entry.author, entry.message, url)

        return msg
    
    def record_processed(self, entry):
        rev = entry.revision.number
        now = datetime.now().isoformat()
        query = "INSERT OR IGNORE INTO svn_log (rev, processed) VALUES (:rev, :now)"
        result = self.db.execute(query, {'rev': rev, 'now': now})
        self.db.connection.commit()

    # Database Functions
    def reset_db(self):
        if os.path.exists(settings.DB_FILE):
            os.remove(settings.DB_FILE)

        db = self.get_db_cursor()
        query = "CREATE TABLE svn_log (rev INTEGER PRIMARY KEY, processed);"
        result = db.execute(query)
        db.connection.commit()
        print query

    def get_db_cursor(self):
        conn = sqlite3.connect(settings.DB_FILE)
        db = conn.cursor()

        return db


    def is_reset_mode(self):
        parser = OptionParser()
        parser.add_option("-R", "--resetdb",
                          action="store_true", dest="reset_db", default=False,
                          help="Reset the db file.")
        (options, args) = parser.parse_args()

        return options.reset_db
