#!/usr/bin/env python
'''
  Copyright (C) 2023 Peter Scott - peterscott@pobox.com

  Version: Mon Jun 12 07:58:38 BST 2023


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

  Purpose
  ~~~~~~~
  I call this very simple programme 'xbiff.py'.  It watches an IMAP
  account and tells you with a beep and a very small message when you
  get a new email.  It occupies no permanent screen space.

  By default, 'xbiff.py' updates the display and beeps when the number
  of unread emails goes up.  The "-a" option causes it to update the
  display (but not to beep) if the number goes down.

  It runs with Python2 or Python3; it has been tested with Python 2.7
  and Python 3.7.


  Invocation
  ~~~~~~~~~~
  If it is on your PATH, 'xbiff.py' can be started by typing:

      xbiff.py&

  However, it should be started in '.bash_profile' and stopped in
  '.bash_logout' under Unix or Linux.


  External programmes used:
  ~~~~~~~~~~~~~~~~~~~~~~~~~
  'kill', 'xmessage' and 'beep'

  'xmessage' is used because it is well documented and, also, because
  I hate Gnome, and desktops in general.

  For 'beep' to work, the command must be owned by root and be setuid
  (chmod 4755).  Without the root setuid, 'beep' only works in terminals.


  Configuration
  ~~~~~~~~~~~~~
  Edit the following constants to suit yourself
'''

SERVER          = 'imap.plus.net'
ACCOUNT_NAME    = 'YOUR_ACCOUNT_NAME'
PASSWORD        = 'YOUR_PASSWORD'
POLL_INTERVAL   = '5'       # minutes, string!

XMESS_COMM = "LANG= xmessage -default okay -geom -0+0 \
-xrm '.Xmessage.Form.Text.scrollVertical:    whenNeeded' \
-xrm '.Xmessage.Form.Text.scrollHorizontal:  whenNeeded' \
-xrm '.Xmessage.*.background:                white' \
-xrm '.Xmessage.*.foreground:                black' \
-xrm '.Xmessage.Form.Text.borderColor:       white' \
-xrm '.Xmessage.Form.Command.foreground:     black' \
-xrm '.Xmessage.Form.Command.background:     green' "

import imaplib, time, socket, sys, re, os
from subprocess import Popen


def alert (message, previousPid = 0, timeout = 0):
  '''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  display a message with 'xmessage'

  There are two kinds of message: email and other.  Email messages have
  no timeout but may be replaced by a new email message.  Other messages
  have a timeout and are prefixed with the script name.
  '''

  xmessComm = XMESS_COMM
  if timeout:
      xmessComm = xmessComm + '-timeout ' + str( timeout) + ' '
      message = NAME + ': ' + message
  pid = Popen( xmessComm + '"' + message + '"', shell=True, close_fds=True).pid
  if pid == 0:
      print( 'Failed to send notification')   # this may look odd in python2.7
      sys.exit( 1)
  time.sleep( 2)            # give new alert time to appear -- to avoid flicker
  eraseAlert( previousPid)
  return pid


def eraseAlert (pid):
  '''~~~~~~~~~~~~~~~~
  Use 'kill' to remove the previous 'xmessage'

  It doesn't matter that 'kill' will fail if the user has already
  OK-ed the previous message
  '''

  if pid:
      junk = Popen( '2> /dev/null kill ' + str( pid), shell=True, \
                                                                close_fds=True)

def usage():
  '''~~~~'''
  sys.stderr.write( 'Usage: ' + NAME + ' [ -a ]\n')
  exit( 1)


def getArgs():
  '''~~~~~~~~~
  get the name of the script and check for the "-a" option
  '''

  global NAME, anyChange

  NAME = os.path.basename( sys.argv [0])
  sys.argv.pop(0)
  if len( sys.argv) == 0:
      return
  if sys.argv [0] != '-a':
       usage()
  else:
       anyChange = True
       sys.argv.pop(0)
  if len( sys.argv) != 0:
      usage()


NAME = ''        # globals
anyChange = False


if __name__ == '__main__':

  unread = previous = xmessagePID = announced = 0
  seconds = int( POLL_INTERVAL) * 60

  getArgs()
  socket.setdefaulttimeout( 10)
  time.sleep( 5)             # give desktop time to appear
  while True:
      connection = None
      try:
          stage = 0
          mail = imaplib.IMAP4_SSL( SERVER)
          connection = mail.socket()
          stage = 1
          mail.login( ACCOUNT_NAME, PASSWORD)
          stage = 2
          status = (mail.status( 'INBOX', '(UNSEEN)')[1][0]).decode()
          unread = int( status.split()[2].rstrip( ')'))
          stage = 3
          mail.logout()
      except Exception as details:
          details = re.sub( "[][(),']", '', str( details))
          if stage == 0:
              announced = alert( "couldn't connect to " + SERVER + \
                                            ' (' + details + ')', 0, seconds+2)
          elif stage == 1:
              announced = alert( "couldn't login to " + SERVER + \
                                            ' (' + details + ')', 0, seconds+2)
          elif stage == 2:
              announced = alert( "couldn't read inbox from " + SERVER + \
                                            ' (' + details + ')', 0, seconds+2)
          else:
              # simpler to treat (unlikely) failed logout as a complete fail
              #
              announced = alert( "couldn't logout from " + SERVER + \
                                            ' (' + details + ')', 0, seconds+2)
          if connection is not None:

               # with python2.7 on fedora 26 imaplib tries to close
               # the socket, but passes on the exception.  The following
               # forces the closure.
               #
               os.closerange( 3,5)

          unread = previous        # i.e. unchanged

      # this isn't needed but it seems to avoid some lengthy waits
      # on the IMAP socket.  See comment above.
      #
      mail = None

      # update alert as needed if unread has changed
      #
      if unread != previous:
          if unread == 0:
              eraseAlert( xmessagePID)
              xmessagePID = 0
          elif anyChange or (unread > previous):
              if unread > previous:
                  junk = Popen( 'beep', shell=False, close_fds=True)
              if unread == 1:
                  ess = ''
              else:
                  ess = 's'
              announced = xmessagePID = alert( str( unread) + \
                                                   ' email' + ess, xmessagePID)

      if not announced:
          announced = alert( 'checking ' + SERVER + ' every ' + \
                                             POLL_INTERVAL + ' minutes', 0, 10)
      previous = unread
      time.sleep( seconds)
