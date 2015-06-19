#!/usr/bin/env python3
"""
    This file is part of BOMtools.

    BOMtools is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BOMTools is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with BOMTools.  If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = 'srodgers'

import configparser
from tkinter import *
from tkinter.ttk import *
import pyperclip
from bommdb import *


defaultMpn = 'N/A'
defaultDb= '/etc/bommgr/parts.db'
defaultConfigLocations = ['/etc/bommgr/bommgr.conf','~/.bommgr/bommgr.conf','bommgr.conf']
firstPn = '800000-101'
defaultMID = 'M0000000'

listFrame = None

#
#
#
#
# Classes for TK GUI
#
#
#
#

#
# Full screen App Class. Sets up TK to use full screen
#


class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>',self.toggle_geom)

    def toggle_geom(self,event):
        geom = self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom


#
# Dialog class
#

class Dialog(Toplevel):

    def __init__(self, parent, title = None, xoffset = 50, yoffset = 50):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+xoffset,
                                  parent.winfo_rooty()+yoffset))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks
    #

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics
    #

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks
    #

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override


#
# Edit Description dialog box
#

class EditDescription(Dialog):
    def __init__(self, parent, title = None, xoffset=50, yoffset=50, values=None, db=None):
        if db is None or values is None or title is None:
            raise SystemError
        self.db = db
        self.values = values
        Dialog.__init__(self, parent, title, xoffset, yoffset)

    def body(self, master):
        Label(master, text='Description').grid(row=0, column=0, sticky=W)
        self.title_entry = Entry(master, width=50)
        partinfo = self.db.lookup_pn(self.values[0])
        if partinfo is None:
            raise SystemError
        self.title_entry.insert(0, partinfo[1])
        self.title_entry.grid(row=0, column=1, sticky=W)

    def validate(self):
        title_entry_text = self.title_entry.get()
        if len(title_entry_text) < 5 or len(title_entry_text) > 50:
            return False
        return True

    def apply(self):
        title_entry_text = self.title_entry.get()
        self.db.update_title(self.values[0], title_entry_text)
        self.values[1] = title_entry_text


#
# Edit Manufacturer's part number dialog box
#

class EditMPN(Dialog):
    def __init__(self, parent, title = None, xoffset=50, yoffset=50, values=None, db=None):
        if db is None or values is None or title is None:
            raise SystemError
        self.db = db
        self.values = values
        Dialog.__init__(self, parent, title, xoffset, yoffset)

    def body(self, master):
        Label(master, text='Manufacturer Part Number').grid(row=0, column=0, sticky=W)
        self.mpn_entry = Entry(master, width=30)
        partinfo = self.db.lookup_mpn(self.values[3])
        if partinfo is None:
            raise SystemError
        self.mpn_entry.insert(0, partinfo[2])
        self.mpn_entry.grid(row=0, column=1, sticky=W)


    def validate(self):
        title_entry_text = self.mpn_entry.get()
        if len(title_entry_text) < 3 or len(title_entry_text) > 30:
            return False
        return True

    def apply(self):
        (pn, mname, mpn, mid) = self.db.lookup_mpn(self.values[3])
        newmpn = self.mpn_entry.get()
        self.db.update_mpn(pn, mpn,
                           newmpn, mid)
        self.values[3] = newmpn



class AddMfgrDialog(Dialog):
    def __init__(self, parent, title="Add Manufacturer", xoffset=50, yoffset=50, new_mfg=None):
        if new_mfg is None:
            raise SystemError
        self.confirm = False
        self.new_mfg = new_mfg
        self.titlestr = title
        Dialog.__init__(self, parent, title, xoffset, yoffset)

    def body(self, master):
        label_text = self.titlestr+': '+self.new_mfg+'?'
        Label(master, text=label_text).pack()


    def apply(self):
        self.confirm = True

    def confirmed(self):
        return self.confirm

#
# Add part dialog box
#

class AddPartDialog(Dialog):
    """
    Add part dialog box
    """
    def __init__(self, parent, title = "Add Part", xoffset=50, yoffset=50, db=None):
        """

        :param parent: Parent window
        :param title: Title of add part dialog box
        :param xoffset: Offset in X direction
        :param yoffset: Offset in Y direction
        :param db: Database object
        :return: N/A
        """
        if db is None or title is None:
            raise SystemError
        self.db = db
        Dialog.__init__(self, parent, title, xoffset, yoffset)

    def new_pn(self):
        """
        Return the next available part number from the database
        :return: Part number string
        """
        res = self.db.last_pn()
        # If this is the very first part number added use the default for firstpn
        if res is None or res[0] is None:
            pn = firstPn
        else:
            pn = res
        (prefix, suffix) = pn.split('-')
        nextnum = int(prefix) + 1
        pn = '{prefix:06d}-{suffix:03d}'.format(prefix=nextnum, suffix=101)
        return pn

    def body(self, master):
        nextpn = self.new_pn()
        self.mfgrs = self.db.get_mfgr_list()
        def_sel = self.mfgrs.index(defaultMfgr)

        Label(master, text='Part Number').grid(row=0, column=0, sticky=W)
        self.pn_entry = Entry(master, width=10)
        self.pn_entry.insert(0, nextpn)
        self.pn_entry.grid(row=0, column=1, sticky=W)

        Label(master, text='Description').grid(row=1, column=0, sticky=W)
        self.desc_entry = Entry(master, width=50)
        self.desc_entry.grid(row=1, column=1, sticky=W)

        Label(master, text='Manufacturer').grid(row=2, column=0, sticky=W)
        self.mfgr_entry = Combobox(master, width=30, values=self.mfgrs)
        self.mfgr_entry.current(def_sel)
        self.mfgr_entry.grid(row=2, column=1, sticky=W)

        Label(master, text='Manufacturer Part Number').grid(row=3, column=0, sticky=W)
        self.mpn_entry = Entry(master, width=30)
        self.mpn_entry.insert(0, defaultMpn)
        self.mpn_entry.grid(row=3, column=1, sticky=W)


    def validate(self):

        # Validate part number
        x = len(self.pn_entry.get())
        if x != 10:
            return False

        # Validate description
        x = len(self.desc_entry.get())
        if x < 5 or x > 50:
            return False

        # Validate manufacturer part number
        x = len(self.mpn_entry.get())
        if x < 3 or x > 30:
            return False

        # Validate manufacturer, and add a new manufacturer if need be
        selected = self.mfgr_entry.get()
        if selected not in self.mfgrs:
            confirm_mfg = AddMfgrDialog(self.parent, new_mfg=selected)
            if confirm_mfg.confirmed() is False:
                return False
            else:
                # Assign a new mid
                mid = self.db.last_mid()
                if mid is not None:
                    mid = int(mid[1:]) + 1
                else:
                    mid = 0
                nextmid = 'M{num:07d}'.format(num=mid)
                # Add manufacturer and MID to manufacturer list
                self.db.add_mfg_to_mlist(selected, nextmid)
                self.mfgrs.append(selected)



        return True

    def apply(self):
        # Retreive all fields
        pn = self.pn_entry.get()
        desc = self.desc_entry.get()
        mfgr = self.mfgr_entry.get()
        mpn = self.mpn_entry.get()

        # Get the mid for the manufacturer name
        res = self.db.lookup_mfg(mfgr)
        if res is None:
            raise SystemError
        mid = res[1]

        # Create the part record and manufacturer part record
        self.db.add_pn(pn, desc, mid, mpn)



#
# Class to show part list
#

class ShowParts:
    def __init__(self, parent, db):
        self.parent = parent
        self.frame = None
        self.db = db
        # create a popup menu
        self.pnpopupmenu = Menu(self.parent, tearoff=0)
        self.pnpopupmenu.add_command(label="Copy part number to clipboard", command=self.copy_pn)
        self.pnpopupmenu.add_command(label="Edit Description",command=self.edit_description)
        self.mpnpopupmenu = Menu(self.parent, tearoff=0)
        self.mpnpopupmenu.add_command(label="Copy manufacturer part number to clipboard", command=self.copy_pn)
        self.mpnpopupmenu.add_command(label="Edit Manufacturer Part Number", command=self.edit_mpn)



    def refresh(self, like=None):
        """
        Refresh screen with current list entries
        :return: N/A
        """
        if(self.frame is not None):
            self.frame.destroy()
        self.frame = Frame(self.parent)
        self.frame.pack(side=TOP, fill=BOTH, expand=Y)
        self.ltree = Treeview(height="26", columns=("Part Number","Description","Manufacturer","Manufacturer Part Number"), selectmode="extended")
        ysb = Scrollbar(orient='vertical', command=self.ltree.yview)
        xsb = Scrollbar(orient='horizontal', command=self.ltree.xview)
        self.ltree.configure(xscroll=xsb.set, yscroll=ysb.set)
        self.ltree.heading('#1', text='Part Number', anchor=W)
        self.ltree.heading('#2', text='Description', anchor=W)
        self.ltree.heading('#3', text='Manufacturer', anchor=W)
        self.ltree.heading('#4', text='Manufacturer Part Number', anchor=W)
        self.ltree.column('#1', stretch=NO, minwidth=0, width=200)
        self.ltree.column('#2', stretch=NO, minwidth=0, width=500)
        self.ltree.column('#3', stretch=NO, minwidth=0, width=300)
        self.ltree.column('#4', stretch=YES, minwidth=0, width=300)
        self.ltree.column('#0', stretch=NO, minwidth=0, width=0) #width 0 for special heading
        self.ltree.bind("<Button-3>", self.popup)

        parts = self.db.get_parts(like)




        for row,(pn,desc) in enumerate(parts):
            mfg = defaultMfgr
            mpn = defaultMpn
            parent_iid = self.ltree.insert("", "end", "", tag=[pn,'partrec'], values=((pn, desc, '', '')))

            # Try to retrieve manufacturer info
            minfo = self.db.lookup_mpn_by_pn(pn)

            if minfo == []: # Use defaults if it no MPN and manufacturer
                minfo =[{'mname':defaultMfgr,'mpn':defaultMpn}]


            for i,item in enumerate(minfo):
                mfg = item['mname']
                mpn = item['mpn']
                #self.ltree.insert("", "end", "", values=((pn, desc, mfg, mpn)), tags=(row))
                self.ltree.insert(parent_iid, "end", "", tag=[pn,'mfgpartrec'], values=(('', '', mfg, mpn)))


        # add tree and scrollbars to frame
        self.ltree.grid(in_=self.frame, row=0, column=0, sticky=NSEW)
        ysb.grid(in_=self.frame, row=0, column=1, sticky=NS)
        xsb.grid(in_=self.frame, row=1, column=0, sticky=EW)
        # set frame resizing priorities
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)


    def popup(self, event):
        """
        Act on right click
        :param event:
        :return: N/A
        """

        # select row under mouse
        iid = self.ltree.identify_row(event.y)
        self.itemid = iid
        if iid:
            # mouse pointer over item
            self.ltree.selection_set(iid)
            item = self.ltree.item(iid)
            self.itemvalues = item['values']
            if item['tags'][1] == 'partrec':
                # Remember part number
                self.pnpopupmenu.tk_popup(event.x_root, event.y_root)
            elif item['tags'][1] == 'mfgpartrec':
                self.mpnpopupmenu.tk_popup(event.x_root, event.y_root)

        else:
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass

    def copy_pn(self):
        """
        Copy part number or manufacturer part number to clipboard
        :return: N/A
        """
        if self.itemvalues[0] != '':
            pyperclip.copy(self.itemvalues[0])
        else:
            pyperclip.copy(self.itemvalues[3])

    def edit_description(self):
        """
        Display Dialog box and allow user to edit part description
        :return: N/A
        """
        title = 'Edit Description: ' + self.itemvalues[0]
        e = EditDescription(self.parent, values=self.itemvalues, db=self.db, title=title)

        #self.refresh()
        self.ltree.item(self.itemid, values=self.itemvalues)

    def edit_mpn(self):
        """
        Display Dialog box and allow user to edit the manufacturer part number
        :return: N/A
        """
        title = 'Edit Manufacturer Part Number: ' + self.itemvalues[3]
        e = EditMPN(self.parent, values=self.itemvalues, db=self.db, title=title)

        self.ltree.item(self.itemid, values=self.itemvalues)
        #self.refresh()


#
# Add a new part number to the database
#

def addPN():
    AddPartDialog(root, db=DB)
    parts.refresh()

#
#
#
#
# Main line code
#
#
#
#
#

if __name__ == '__main__':


   ## Customize default configurations to user's home directory

    for i in range(0, len(defaultConfigLocations)):
        defaultConfigLocations[i] = os.path.expanduser(defaultConfigLocations[i])


    # Read the config file
    config = configparser.ConfigParser()

    configLocation = defaultConfigLocations

    config.read(configLocation)

    try:
        general = config['general']
    except KeyError:
        print('Error: no config file found')
        sys.exit(2)

    # Open the database file


    db = os.path.expanduser(general.get('db', defaultDb))

    # Check to see if we can access the database file and that it is writable

    if(os.path.isfile(db) == False):
        print('Error: Database file {} doesn\'t exist'.format(db))
        raise(SystemError)
    if(os.access(db,os.W_OK) == False):
        print('Error: Database file {} is not writable'.format(db))
        raise(SystemError)

    DB = BOMdb(db)

    # Look up default manufacturer

    res = DB.lookup_mfg_by_id(defaultMID)
    if(res is None):
        defaultMfgr = 'Default MFG Error'
    else:
        defaultMfgr = res[0]

    # Set up the TCL add window

    root = Tk()
    root.title("Part Manager")
    app=FullScreenApp(root)

    parts = ShowParts(root, DB)

    menubar = Menu(root, tearoff = 0)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    # display the menu
    root.config(menu=menubar)

    editmenu = Menu(menubar, tearoff = 0)
    menubar.add_cascade(label="Edit", menu=editmenu)
    editmenu.add_command(label="Add part number", command=addPN)


    viewmenu = Menu(menubar, tearoff = 0)
    viewmenu.add_command(label="Refresh", command=parts.refresh)
    menubar.add_cascade(label="View", menu=viewmenu)


    # display the menu
    root.config(menu=menubar)

    parts.refresh()

    root.mainloop()