############################################################################
##
## Copyright (C) 2007 Alexander Macdonald. All rights reserved.
##
## Modified by QB89Dragon 2009 for inclusion to pen tablet utility
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License version 2
##
## Graphics Tablet Applet
##
############################################################################

#import pyGtk
#pyGtk.require('2.0')
#import Gtk
#import Gtk.glade
#import gobject
#import cairo
import gi
from gi.repository import Gtk
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk
import sys
import os
import subprocess
import math

def GetPressCurve(devicename):

	try:
		output = subprocess.Popen(["xsetwacom", "-x", "get", devicename, "PressureCurve"], stdout=subprocess.PIPE).communicate()[0]
		bits = output.split()
		if bits[1] == "\"PressureCurve\"":
			return [float(x.replace("\"","")) for x in bits[2:6]]
	except:
		return None

def SetPressCurve(devicename, points):

	try:
		output = subprocess.Popen(["xsetwacom", "set", devicename, "PressureCurve", str(points[0]), str(points[1]), str(points[2]), str(points[3])])
	except:
		return None
	
def GetThreshold(devicename):

	try:
		output = subprocess.Popen(["xsetwacom", "get", devicename, "Threshold"], stdout=subprocess.PIPE).communicate()[0]
		if len(output.strip()) == 0:
			return None
		else:
			return float(output.strip())
	except:
		return None

def SetThreshold(devicename, force):

	try:
		output = subprocess.Popen(["xsetwacom", "set", devicename, "Threshold", str(force)])
	except:
		return None

ListMode = ["Relative", "Absolute"]

def GetMode(devicename):

	try:
		output = subprocess.Popen(["xsetwacom", "get", devicename, "Mode"], stdout=subprocess.PIPE).communicate()[0]
		for index in range(len(ListMode)):
			if output.strip() == ListMode[index]:
				return index
	except:
		return None

def SetMode(devicename, m):

	try:
		#print "xsetwacom "+ "set "+ devicename + " Mode " + ListMode[m]
		output = subprocess.Popen(["xsetwacom", "set", devicename, "Mode", ListMode[m]])
		return int(output.strip())
		#return output.strip()
	except:
		return None

def SetAccelProfile(devicename, m):

	try:
		cmd = "xinput set-prop '%s' 'Device Accel Profile' %d" %(devicename, m)
		output = os.popen(cmd)
		return int(output.strip())
	except:
		print "SetAccelProfile except"
		return None
		
def GetAccelProfile(device):
	try:
		output = os.popen("xinput list-props '"+device+"'")
		data = output.readlines()
		for line in data:
			if line.find('Device Accel Profile') != -1:
				data = int(line.split(":")[1])
				return data
	except:
		return None
	

def SetAdapt(devicename, a):
	#print "xinput "+ "set-prop \"" + devicename + "\" --type=float \"Device Accel Adaptive Deceleration\" " + a
	output = subprocess.Popen(["xinput", "set-prop", devicename, "--type=float", "Device Accel Adaptive Deceleration", a])
	print output
	#return  int(output)
	#return int(output.strip())

def GetAdapt(device):
	try:
		cmd = "xinput list-props '%s'" % device
		output = os.popen(cmd)
		data = output.readlines()
		for line in data:
			if line.find('Adaptive Deceleration') != -1:
				data = float(line.split(":")[1])
				return data
	except:
		return 1.0


def SetConst(devicename, a):
	output = subprocess.Popen(["xinput", "set-prop", devicename, "--type=float", "Device Accel Constant Deceleration", a])
	return int(output.strip())

def GetConst(device):
	try:
		cmd = "xinput list-props '%s'" % device
		output = os.popen(cmd)
		data = output.readlines()
		for line in data:
			if line.find('Constant Deceleration') != -1:
				data = float(line.split(":")[1])
				return data
	except:
		return 1.0


class PressureCurveWidget(Gtk.DrawingArea):
	
	def __init__(self):

		Gtk.DrawingArea.__init__(self)
		
		self.Points = [0,100,100,0]
		self.Pressure = 0.0
		
		self.Radius = 5.0
		self.ControlPointStroke = 2.0
		self.ControlPointDiameter = (self.Radius * 2) + self.ControlPointStroke
		self.WindowSize = None
		self.Scale = None
		
		self.Threshold = None
		
		self.DeviceName = ""
		
		self.DraggingCP1 = False
		self.DraggingCP2 = False
		self.DraggingCF = False

		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK  | Gdk.EventMask.BUTTON_MOTION_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK | Gdk.EventMask.BUTTON2_MOTION_MASK | Gdk.EventMask.BUTTON3_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
		
		self.connect("configure-event", self.ConfigureEvent)
		# self.connect("expose-event", self.ExposeEvent)
		self.connect("motion-notify-event", self.MotionEvent)
		self.connect("button-press-event", self.ButtonPress)
		self.connect("button-release-event", self.ButtonRelease)
		self.set_size_request(100,100)
		#self.do_realize()

	def SetDevice(self, name):
		self.DeviceName = name
		self.Threshold = GetThreshold(name)
		
		if self.Threshold != None:
			self.Threshold *= (100.0 / 19.0)
			
		points = GetPressCurve(name)
		if points == None:
			self.Points = None
		else:
			self.Points = [points[0], 100.0 - points[1], points[2], 100.0 - points[3]]
	
	def Update(self):
		if not isinstance(self.window, Gdk.Window):
			return
		self.window.invalidate_region(self.window.get_clip_region(), True)
	
	def ClampValue(self, v):
		if v < 0.0:
			return 0.0
		elif v > 100.0:
			return 100.0
		else:
			return v
	
	def ConfigureEvent(self, widget, event):
		
		self.WindowSize = self.window.get_size()
		self.Scale = ((self.WindowSize[0] - self.ControlPointDiameter) / 100.0, (self.WindowSize[1] - self.ControlPointDiameter) / 100.0)
	
	def MotionEvent(self, widget, event):

		pos = event.get_coords()
		pos = (pos[0] / self.Scale[0], pos[1] / self.Scale[1])
		
		if self.Points == None:
			return

		if self.DraggingCP1:
			
			self.Points[0] = self.ClampValue(pos[0])
			self.Points[1] = self.ClampValue(pos[1])
		
		elif self.DraggingCP2:
			
			self.Points[2] = self.ClampValue(pos[0])
			self.Points[3] = self.ClampValue(pos[1])
		
		elif self.DraggingCF:
			
			self.Threshold = int(self.ClampValue(pos[0]) / (100.0 / 19)) * (100.0 / 19)
	
	def ButtonPress(self, widget, event):
		
		if self.Points == None:
			return
		
		if self.DraggingCP1 or self.DraggingCP2 or self.DraggingCF:
			self.DragFinished()
		else:
			pos = event.get_coords()
			pos = (pos[0] / self.Scale[0], pos[1] / self.Scale[1])

			if pos[0] > (self.Points[0] - self.ControlPointDiameter) and pos[0] < (self.Points[0] + self.ControlPointDiameter):
				
				if pos[1] > (self.Points[1] - self.ControlPointDiameter) and pos[1] < (self.Points[1] + self.ControlPointDiameter):
					
					self.DraggingCP1 = True
					return
			
			if pos[0] > self.Points[2] - self.ControlPointDiameter and pos[0] < self.Points[2] + self.ControlPointDiameter:
				
				if pos[1] > self.Points[3] - self.ControlPointDiameter and pos[1] < self.Points[3] + self.ControlPointDiameter:
					
					self.DraggingCP2 = True
					return
			
			if pos[0] > self.Threshold - self.ControlPointDiameter and pos[0] < self.Threshold + self.ControlPointDiameter:
				
				self.DraggingCF = True
				return

	def ButtonRelease(self, widget, event):
		
		self.DragFinished()
	
	def DragFinished(self):
		if self.Points != None:
			#if self.DraggingCP1:	# Update to new curve constraints
			#	self.Points[3] = self.Points[0]
			#	self.Points[2] = self.Points[1]
			#elif self.DraggingCP2:
			#	self.Points[0] = self.Points[3]
			#	self.Points[1] = self.Points[2]
			#print int(self.Points[0]), int(100.5 - self.Points[1]), int(self.Points[2]), int(100.5 - self.Points[3])
				
			SetPressCurve(self.DeviceName, [int(self.Points[0]+.5), int(100.5 - self.Points[1]), int(self.Points[2]+.5), int(100.5 - self.Points[3])])
		if self.Threshold != None:
			SetThreshold(self.DeviceName, int(self.Threshold / (100.0 / 19.0)) + 1)
		self.DraggingCP1 = self.DraggingCP2 = self.DraggingCF = False
		

	def ExposeEvent(self, widget, event):
		cr = widget.window.cairo_create()
		cr.set_line_cap(cairo.LINE_CAP_ROUND);

		cr.save()
		cr.translate(self.ControlPointDiameter / 2.0, self.ControlPointDiameter / 2.0)

		# Grid
		cr.set_line_width(0.5)
		cr.set_source_rgba(0.0, 0.0, 0.0, 0.25)
		cr.save()
		cr.scale(self.Scale[0], self.Scale[1])
		cr.new_path()
		for x in range(11):
			cr.move_to(x * 10.0, 0.0)
			cr.line_to(x * 10.0, 100.0)
		for y in range(11):
			cr.move_to(0.0, y * 10.0)
			cr.line_to(100.0, y * 10.0)
		cr.restore()
		cr.stroke()
		
		if self.Pressure != None:
		
			# Linear Line
			cr.set_line_width(1.0)
			
			cr.save()
			cr.scale(self.Scale[0], self.Scale[1])
			cr.new_path()
			cr.move_to(0.0, 100.0)
			cr.line_to(100.0, 0.0)
			cr.restore()
			cr.stroke()
			
			# Click Force
			
			if self.Threshold != None:
				cr.set_line_width(1.0)
				cr.set_source_rgba(1.0, 0.0, 0.0, 0.25)
				cr.save()
				cr.scale(self.Scale[0], self.Scale[1])
				cr.new_path()
				cr.move_to(self.Threshold, 0.0)
				cr.line_to(self.Threshold, 100.0)
				cr.restore()
				cr.stroke()
				
			
			if self.Points == None:
				points = [0.0, 100.0, 100.0, 0.0]
			else:
				points = self.Points

			# Pressure
			cr.save()
			cr.scale(self.Scale[0], self.Scale[1])
			cr.rectangle(0.0, 0.0, self.Pressure * 100.0, 100.0)
			cr.clip()
			cr.new_path()
			cr.set_source_rgba(114.0 / 255.0, 159.0 / 255.0, 207.0 / 255.0, 0.5)
			cr.move_to(0.0,100.0)
			cr.curve_to(points[0], points[1], points[2], points[3], 100.0, 0.0)
			cr.line_to(100.0, 100.0)
			cr.fill()
			cr.restore()
			
			# Pressure Curve
			cr.set_line_width(2.0)
			cr.set_source_rgba(32.0 / 255.0, 74.0 / 255.0, 135.0 / 255.0, 1.0)
			cr.save()
			cr.scale(self.Scale[0], self.Scale[1])
			cr.new_path()
			cr.move_to(0.0,100.0)
			cr.curve_to(points[0], points[1], points[2], points[3], 100.0, 0.0)
			cr.restore()
			cr.stroke()
			
			if self.Points != None:
				# Control Lines
				cr.set_line_width(2.0)
				cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
				cr.save()
				cr.scale(self.Scale[0], self.Scale[1])
				cr.move_to(0.0,100.0)
				cr.line_to(self.Points[0], self.Points[1])
				cr.move_to(100.0,0.0)
				cr.line_to(self.Points[2], self.Points[3])
				cr.restore()
				cr.stroke()

				# Control Points
				cr.set_line_width(2.0)
				cr.save()
				cr.arc(self.Points[0] * self.Scale[0], self.Points[1] * self.Scale[1], self.Radius, 0.0, 2.0 * math.pi);
				cr.set_source_rgba(237.0 / 255.0, 212.0 / 255.0, 0.0, 0.5)
				cr.fill_preserve()
				cr.set_source_rgba(239.0 / 255.0, 41.0 / 255.0, 41.0 / 255.0, 1.0)
				cr.stroke()
				cr.arc(self.Points[2] * self.Scale[0], self.Points[3] * self.Scale[1], self.Radius, 0.0, 2.0 * math.pi);
				cr.set_source_rgba(237.0 / 255.0, 212.0 / 255.0, 0.0, 0.5)
				cr.fill_preserve()
				cr.set_source_rgba(239.0 / 255.0, 41.0 / 255.0, 41.0 / 255.0, 1.0)
				cr.stroke()
				cr.restore()
		cr.restore()

class DrawingTestWidget(Gtk.DrawingArea):
	
	def __init__(self):

		Gtk.DrawingArea.__init__(self)
		
		self.Device = 0
		self.Radius = 5.0
		self.Drawing = False
		self.WindowSize = None
		self.Raster = None
		self.RasterCr = None
		
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK  | Gdk.EventMask.BUTTON_MOTION_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK | Gdk.EventMask.BUTTON2_MOTION_MASK | Gdk.EventMask.BUTTON3_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
		
		self.connect("configure-event", self.ConfigureEvent)
		self.connect("map-event", self.ExposeEvent)
		self.connect("motion-notify-event", self.MotionEvent)
		self.connect("button-press-event", self.ButtonPress)
		self.connect("button-release-event", self.ButtonRelease)
		self.set_size_request(100,100)
		#self.do_realize()

	def ConfigureEvent(self, widget, event):
		
		self.WindowSize = self.window.get_size()
		self.Raster = self.window.cairo_create().get_target().create_similar(cairo.CONTENT_COLOR, self.WindowSize[0], self.WindowSize[1])
		self.RasterCr = cairo.Context(self.Raster)
		self.RasterCr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		self.RasterCr.rectangle(0.0, 0.0, self.WindowSize[0], self.WindowSize[1])
		self.RasterCr.fill()
	
	def GetPressure(self):
		#dev = Gdk.devices_list()[self.Device]
		dev = Gdk.DeviceManager.list_devices(Gdk.DeviceManager, 2)[self.Device]
		state = dev.get_state(self.window)
		return dev.get_axis(state[0], Gdk.AXIS_PRESSURE)
	
	def MotionEvent(self, widget, event):

		if self.Drawing:
			pos = event.get_coords()
			p = self.GetPressure()
			if p == None:
				p = 0.0
			r =  p * 50 + 5
			self.RasterCr.set_line_width(2)
			self.RasterCr.set_source_rgba(p, 1.0, 0.0, 0.5)
			self.RasterCr.arc(pos[0], pos[1],r, 0.0, 2 * math.pi);
			self.RasterCr.fill_preserve()
			self.RasterCr.set_source_rgba(0.5, 0.2, p, 0.5)
			self.RasterCr.stroke()
			reg = Gdk.Region()
			reg.union_with_rect((int(pos[0] - r - 2), int(pos[1] - r - 2), int(2 * (r + 2)), int(2 * (r + 2))))
			self.window.invalidate_region(reg, False)
	
	def ButtonPress(self, widget, event):
		
		self.Drawing = True

	def ButtonRelease(self, widget, event):
		
		self.Drawing = False

	def ExposeEvent(self, widget, event):
		cr = widget.window.cairo_create()
		cr.set_source_surface(self.Raster, 0.0, 0.0)
		cr.paint()
		cr.set_line_width(2)
		cr.set_source_rgba(0.0, 0.0, 0.0, 0.25)
		cr.rectangle(0.0, 0.0, self.WindowSize[0], self.WindowSize[1])
		cr.stroke()

class GraphicsTabletApplet:
	
	def __init__(self, window, wTree, Device):
		self.Active = 0	# Control
		self.InLoop = 0 # Flag
		self.WidgetTree = wTree
		self.MainWindow = window
		self.DrawingTestFrame = self.WidgetTree.get_object("drawingalignment")
		self.PressureVBox = self.WidgetTree.get_object("pressurevbox")
		self.DeviceModeCombo = self.WidgetTree.get_object("devicemodecombo")
		self.HomotheticMapCheck = self.WidgetTree.get_object("homotheticmap")
		self.XScreenX = self.WidgetTree.get_object("xscreenx")
		self.XScreenY = self.WidgetTree.get_object("xscreeny")
		self.XTilt = self.WidgetTree.get_object("xtilt")
		self.YTilt = self.WidgetTree.get_object("ytilt")
		
		self.AccelProfileCombo = self.WidgetTree.get_object("accelprofilecombo")
		self.Adapt = self.WidgetTree.get_object("adapt")
		self.Const = self.WidgetTree.get_object("const")		
		
		self.Curve = PressureCurveWidget()
		self.Curve.show()
		self.PressureVBox.add(self.Curve)
		
		self.DrawingArea = DrawingTestWidget()
		self.DrawingArea.show()
		self.DrawingTestFrame.add(self.DrawingArea)
		
		for i in range(0,len(Gdk.DeviceManager.list_devices(Gdk.DeviceManager, 0))):
			item = Gdk.devices_list()[i].name
			if item == Device:
				self.Device = i
		self.DeviceMode = None
		self.DeviceName = Device
		
		self.DrawingArea.Device = self.Device
		self.DeviceName = Gdk.devices_list()[self.Device].name
		self.Curve.SetDevice(self.DeviceName)
		self.UpdateDeviceMode()
		self.UpdateDeviceProfile()
		self.UpdateAdapt()
		self.UpdateConst()

		self.DeviceModeCombo.connect("changed", self.ModeChanged)
		self.AccelProfileCombo.connect("changed", self.ProfileChanged)
		self.Adapt.connect("value-changed", self.AdaptChanged)
		self.Const.connect("value-changed", self.ConstChanged)

		self.DrawingArea.set_extension_events(Gdk.EXTENSION_EVENTS_ALL)

	def Run(self):
		self.Active = 1
		self.InLoop = 1
		self.DeviceName = Gdk.devices_list()[self.Device].name
		self.UpdateDeviceMode()
		self.UpdateDeviceProfile()
		gobject.timeout_add(20, self.Update)

	def Stop(self):
		self.Active = 0

	def GetPressure(self):
		dev = Gdk.devices_list()[self.Device]
		if not isinstance(self.DrawingArea.window, Gdk.Window):
			return (0.0, 0.0)
		state = dev.get_state(self.DrawingArea.window)
		return dev.get_axis(state[0], Gdk.AXIS_PRESSURE)

	def GetTilt(self):
		dev = Gdk.devices_list()[self.Device]
		state = dev.get_state(self.MainWindow.window)
		try:
			x = float(dev.get_axis(state[0], Gdk.AXIS_XTILT))
			y = float(dev.get_axis(state[0], Gdk.AXIS_YTILT))
			if x != x or y != y:
				return (0.0, 0.0)
			else:
				return (x, y)
		except:
			return (0.0, 0.0)
	
	def AdaptChanged(self, event):
		dev = Gdk.devices_list()[self.Device]
		AdaptDecel = self.Adapt.get_value()
		SetAdapt(self.DeviceName, str(AdaptDecel))
	
	def ConstChanged(self, event):
		dev = Gdk.devices_list()[self.Device]
		ConstDecel = self.Const.get_value()
		SetConst(self.DeviceName, str(ConstDecel))

			
	def ModeChanged(self, widget):
		SetMode(self.DeviceName, widget.get_active())
	
	def ProfileChanged(self, widget):
		SetAccelProfile(self.DeviceName, widget.get_active())
	
	def UpdateDeviceMode(self):
		self.DeviceMode = GetMode(self.DeviceName)
		if self.DeviceMode == None:
			self.DeviceModeCombo.set_sensitive(False)
		else:
			self.DeviceModeCombo.set_sensitive(True)
			self.DeviceModeCombo.set_active(self.DeviceMode)
	
	def UpdateDeviceProfile(self):
		self.DeviceProfile = GetAccelProfile(self.DeviceName)
		if self.DeviceProfile == None:
			self.AccelProfileCombo.set_sensitive(False)
		else:
			self.AccelProfileCombo.set_sensitive(True)
			self.AccelProfileCombo.set_active(self.DeviceProfile)

	def UpdateAdapt(self):
		AdaptDecel = GetAdapt(self.DeviceName)
		#print "Adapt : %f" % AdaptDecel
		self.Adapt.set_value(AdaptDecel)		

	def UpdateConst(self):
		ConstDecel = GetConst(self.DeviceName)
		#print "Const : %f" % ConstDecel
		self.Const.set_value(ConstDecel)		
	
	def DeviceSelected(self, widget):
		self.Device = widget.get_active()
		self.DrawingArea.Device = self.Device
		self.DeviceName = Gdk.devices_list()[self.Device].name
		self.Curve.SetDevice(self.DeviceName)
		self.UpdateDeviceMode()
		self.UpdateDeviceProfile()

	def Update(self):
		p = self.GetPressure()
		if p == None:
			self.Curve.Pressure = None
			self.Curve.Update()
		else:
			self.Curve.Pressure = p
			self.Curve.Update()
	
		t = self.GetTilt()
	
		self.XTilt.set_adjustment(Gtk.Adjustment(t[0], -1.0, 1.0))
		self.YTilt.set_adjustment(Gtk.Adjustment(t[1], -1.0, 1.0))
		
		if self.Active:
			return True
		else:
			self.InLoop = 0

################################################################################
