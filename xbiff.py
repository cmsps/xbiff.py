#!/usr/bin/env python
'''
  Copyright (C) 2017 Peter Scott - p.scott@shu.ac.uk

  Licence
  ~~~~~~~
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published
  by the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  Version
  ~~~~~~~
  Thu Nov 9 17:43:57 GMT 2017


  Purpose
  ~~~~~~~
  I call this very simple programme 'xbiff.py'.  It watches an IMAP
  account and tells you with a beep and a very small message when you
  get a new email.  It occupies no permanent screen space.


  Invocation
  ~~~~~~~~~~
  If it is on your PATH, 'xbiff.py' can be started by typing:

      xbiff.py&

  However, it should be started in '.bash_profile' and stopped in
  '.bash_logout' under Unix or Linux.


  Other programmes used
  ~~~~~~~~~~~~~~~~~~~~~
  'xmessage' and 'beep'

  'xmessage' is used because it is neater than GTK notifications and
  better documented.

  For 'beep' to work, the command must be owned by root and be setuid
  (chmod 4755).  Without the root setuid, 'beep' only works in terminals.


  Configuration
  ~~~~~~~~~~~~~
  Edit the following constants to suit yourself
'''

SERVER          = 'imap.gmail.com'
ACCOUNT_NAME    = 'YOUR_ACCOUNT_NAME'
PASSWORD        = 'YOUR_PASSWORD'
POLL_INTERVAL   = 2                    # minutes


import imaplib, time, os
from subprocess import *


def alert (message, previousPid, timeout):
  ''' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    display a message with 'xmessage'

    There are two kinds of message: email and other.  Email messages
    are the main ones; they have no timeout but can be replaced with a
    new message.  Other messages have a timeout.
  '''

  xmessComm = 'LANG= xmessage -default okay -geom -1366+0 \
                  -xrm ".Xmessage.Form.Text.scrollVertical:    whenNeeded" \
                  -xrm ".Xmessage.Form.Text.scrollHorizontal:  whenNeeded" \
                  -xrm ".Xmessage.*.background:                white" \
                  -xrm ".Xmessage.*.foreground:                black" \
                  -xrm ".Xmessage.Form.Text.borderColor:       white" \
                  -xrm ".Xmessage.Form.Command.foreground:     black" \
                  -xrm ".Xmessage.Form.Command.background:     green"'
  if timeout:
      xmessComm = xmessComm + ' -timeout ' + str(timeout)
  pid = Popen( xmessComm + ' "' + message + '"', shell=True).pid
  if pid == 0:
      print 'Failed to send notification'
      sys.exit( 1)
  time.sleep( 2)             # give new xmess time to appear to avoid flicker
  eraseAlert( previousPid)
  return pid


def eraseAlert (pid):
  ''' ~~~~~~~~~~~~~~~
    Use 'kill' to remove the previous 'xmessage'

    It doesn't matter that 'kill' will fail if the user has already
    OK-ed the previous message
  '''

  if pid:
      junk = Popen( '2> /dev/null kill ' + str(pid), shell=True)


if __name__ == '__main__':

    unread = previous = xmessagePID = announced = 0
    seconds = POLL_INTERVAL * 60

    time.sleep( 5)             # give desktop time to appear
    while True:
        try:
            mail = imaplib.IMAP4_SSL( SERVER)
            mail.login( ACCOUNT_NAME, PASSWORD)
            status = mail.status( 'INBOX', '(RECENT UNSEEN MESSAGES)')[1][0]
            mail.logout()
            os.close( 3)    # avoid passing socket to children
            unread = int( status.split()[6].rstrip( ')'))

        except:
            try:                   # avoid passing socket to children
                os.close( 3)
            except:
                pass
            announced = alert( "xbiff.py: couldn't login to " + SERVER, + \
                                                                  0, seconds+2)
            unread = previous

        if unread != previous:
            if unread == 0:
                eraseAlert( xmessagePID)
                xmessagePID = 0
            else:
                if unread > previous:
                    if unread == 1:
                        ess = '"'
                    else:
                        ess = 's"'
                    junk = Popen( 'beep', shell=True)
                    announced = xmessagePID = alert( str(unread) + \
                                               '" email' + ess, xmessagePID, 0)

        if not announced:
            announced = alert( "xbiff.py: checking " + SERVER + " every " + \
                                        str(POLL_INTERVAL) + " minutes", 0, 10)
        previous = unread
        time.sleep( seconds)
