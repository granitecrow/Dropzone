## \file  dropzone.py
#  \brief Dropzone Game
#  \author Jeffrey Cusato
#  \date 2011
#  \version 1.0
#
#  Dropzone is a stupid game I made in spare time in an attempt to learn python
#  and all the fun things that do with it.
#
#  I grabbed a menu class from some dude to make moving through the dialogs
#  much easier.
#
#  Have fun playing!
#
#
#       Copyright 2011 Jeffrey Cusato
#

#-------------------------------------------------------------------------------
#---[ Imports ]-----------------------------------------------------------------
#-------------------------------------------------------------------------------
try:
	import pygame
	import pygame._view # py2exe says it can't find it
	import random
	import os
	import math
	import time
	import sys
	from menu import *
	os.environ['SDL_VIDEO_CENTERED'] = '1'
except ImportError, err:
	print "Could not load module. %s" % (err)
	sys.exit(2)


#-------------------------------------------------------------------------------
#---[ Defines ]-----------------------------------------------------------------
#-------------------------------------------------------------------------------
### Set True Value
TRUE = 1

### Set False Value
FALSE = 0

### Set left mouse-click values
LEFT = 1

### Set screen width and height
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

### RGB color for black
BLACK = (0, 0, 0)

### RGB color for white
WHITE = (255, 255, 255)

### RGB color for all in-game text
OFFWHITE = (255, 250, 210)
	
#Initialize Pygame
pygame.init()

#Create a window of 640x480 pixels
#screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

### Black background the size of the game-playing screen
BLKSCREEN = pygame.Surface(screen.get_size())
BLKSCREEN = BLKSCREEN.convert()
BLKSCREEN.fill(BLACK)

### White background the size of the game-playing screen
WHTSCREEN = pygame.Surface(screen.get_size())
WHTSCREEN = WHTSCREEN.convert()
WHTSCREEN.fill(WHITE)	

# create a background for drawing onto during the game; calling it BLKSCREEN
# in-game is confusing
background = BLKSCREEN

#set background and screen params
screen.blit(BLKSCREEN, (0, 0))

#-------------------------------------------------------------------------------
#---[ Resource Handlers ]-------------------------------------------------------
#-------------------------------------------------------------------------------
## This loads and image in the data directory and returns an image and image rect
#  @param	name		The name of the image to load
def load_image(filename):
	fullname = os.path.join('data', filename)
	try:
		image = pygame.image.load(fullname)
		if image.get_alpha() is None:
			image = image.convert()
		else:
			image = image.convert_alpha()
	except pygame.error, message:
		print 'Could not load image: ', fullname
		raise SystemExit, message
	return image, image.get_rect()

def load_sliced_sprites(w, h, filename):
	fullname = os.path.join('data', filename)
	images = []
	master_image = pygame.image.load(fullname).convert_alpha()
	
	master_width, master_height = master_image.get_size()
	for i in xrange(int(master_width/w)):
		images.append(master_image.subsurface((i*w,0,w,h)))
	return images

## This loads the high score list from the filesystem
def parse_highscores():
	"""Parses the high score table and returns a
	list of scores and their owners"""
	highscorefile = 'highscores.txt'
	if os.path.isfile(highscorefile):
		# read the file into lines
		f = open(highscorefile, 'r')
		lines = f.readlines()
		# break lines into length 2 lists [name, score]
		scores = []
		for line in lines:
			scores.append( line.strip().split(':'))
		return scores
	else:
		# generate default highscore table
		f = open(highscorefile, 'w')
		f.write("""Smoke:10000
	Corndog:9000
	Skyking:8000
	Misty:7000
	Casino:6000
	Thug:5000
	Whiskey:4000
	Tahoe:3000
	Razor:2000
	Garbo:1000""")
		f.close()
		# call method again - will load the scores we just wrote this time
		return parse_highscores()

def render_textrect(string, font, rect, text_color, background_color, justification=0):
	"""Returns a surface containing the passed text string, reformatted
	to fit within the given rect, word-wrapping as necessary. The text
	will be anti-aliased.
	"""
	#	@param	string				The text you wish to render. \n begins a new line
	#	@param	font				A font object
	#	@param	rect				a rectangle giving the size of the surface requested
	#	@param	text_color			A 3-byte tuple of the RGB value of text color (eg (0,0,0)=black)
	#	@param	background_color	A 3-byte tuple of the RGB value of the surface
	#	@param	justification		0 (default): left-justified
	#								1 horizontally centered
	#								2 right-justified

	final_lines = []
	requested_lines = string.splitlines()
	# Create a series of lines that will fit on the provided rectangle
	for requested_line in requested_lines:
		if font.size(requested_line)[0] > rect.width:
			words = requested_line.split(' ')
			# if any words are too long to fit then return
#			for word in words:
#				if font.size(word)[0] >= rect.width:
#					raise self.message = "The word is too long to fit in the rect passed"
			# start a new line
			accumulated_line = ""
			for word in words:
				test_line = accumulated_line + word + " "
				# build the line while the words fit
				if font.size(test_line)[0] < rect.width:
					accumulated_line = test_line
				else:
					final_lines.append(accumulated_line)
					accumulated_line = word + " "
			final_lines.append(accumulated_line)
		else:
			final_lines.append(requested_line)
	
	surface = pygame.Surface(rect.size)
	surface.fill(background_color)
	
	accumulated_height = 0
	for line in final_lines:
#		if accumulated_height + font.size(line)[1] >= rect.height:
#			raise self.message = "Once word wrapped, the string is too tall to fit in the rect"
		if line != "":
			tempsurface = font.render(line, 1, text_color)
			if justification == 0:
				surface.blit(tempsurface, (0, accumulated_height))
			elif justification == 1:
				surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
			elif justification == 2:
				surface.blit(tempsurface, (rect.width - tempsureface.get_width(), accumulated_height))
#			else:
#				raise self.message = "Invalid justificaton argument"
		accumulated_height += font.size(line)[1]
	return surface
	
## Decorator for functions to handle how many times a function has run
def run_once(f):
	def wrapper(*args, **kwargs):
		if not wrapper.has_run:
			wrapper.has_run = True
			return f(*args, **kwargs)
	wrapper.has_run = False
	return wrapper	
#-------------------------------------------------------------------------------
#---[ Game Objects ]------------------------------------------------------------
#-------------------------------------------------------------------------------
class Plane(pygame.sprite.Sprite):
	## The Constructor
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("c130.png")
		self.hitCARP = FALSE
		self.dy_offset = 0
		
		self.sndBeenHit = pygame.mixer.Sound("audio\boom.wav")
		self.sndBeenHit.set_volume(0.5)
		self.sndMetal = pygame.mixer.Sound("audio\metal.wav")
		self.sndMetal.set_volume(0.2)
		self.sndThunder = pygame.mixer.Sound("audio\lightning.wav")
		self.sndThunder.set_volume(0.2)
		self.sndEngine = pygame.mixer.Sound("audio\C-130.wav")
		self.sndEngine.set_volume(1.0)

			
	## Update Method called on each clock tick
	def update(self):
		mousex, mousey = pygame.mouse.get_pos()
		if self.hitCARP == TRUE:
			self.dy_offset += -15
			mousey += self.dy_offset
		else:
			if mousey < (screen.get_height() * 0.1): mousey = (screen.get_height() * 0.1)
			if mousey > (screen.get_height() * 0.9): mousey = (screen.get_height() * 0.9)
		self.rect.center = (mousex, mousey)
			
	def greenlight(self):
		self.hitCARP = TRUE
class Payload(pygame.sprite.Sprite):
	def __init__(self, release_point):
		pygame.sprite.Sprite.__init__(self)
		# load spritesheet for payload image
		payloadimages = load_sliced_sprites(30, 25, 'chute_spritesheet.png')
		self._images = payloadimages
		self._frame = 0
		self.image = self._images[self._frame]
		self.rect = self.image.get_rect()
		
		self.rect.center = release_point
		self.setup()
		self.framecounter = 0
		
		self.isLanded = False
		
	def update(self):
		if self.isLanded == False:
			self.framecounter += 1
			
			#TODO: set dx and dy to random wind tuple
			#TODO: rotate image of parachute; or cycle through spritesheet
			
			self.rect.centerx += self.dx
			self.rect.centery += self.dy
			#TODO: stop payload from drifting off-screen (left & right)
			if (self.framecounter >= 30):
				self.dx = 0
				self.dy = 0
				# once landed, set payload image to crate
				self._frame += 1
				self.image = self._images[self._frame]
				self.isLanded = True
		
	
	def setup(self):
		self.dy = random.randrange(-2, 2)
		self.dx = random.randrange(-2, 2)
		
class USAFlogo(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("airforce.gif")
		self.rect = self.image.get_rect()
		self.reset()
				
		self.dy = 20
		
	def update(self):
		self.rect.centery += self.dy
		if self.rect.top > screen.get_height():
			self.reset()
				
	def reset(self):
		self.rect.top = 0
		self.rect.centerx = random.randrange(0, screen.get_width())
		self.rect.centery = -150

	def greenlight(self):
		self.dy = 0

class Target(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("target.png")
		self.rect = self.image.get_rect()
		self.reset()
		self.dy = 20
		
	def update(self):
		self.rect.centery += self.dy
		if self.rect.top > screen.get_height():
			self.reset()
				
	def reset(self):
		self.rect.centerx = random.randrange(0, screen.get_width())
		self.rect.centery = -5000 #default

	def greenlight(self):
		self.dy = 0	
class Artillery(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		# load spritesheet for explosion
		artilleryimages = load_sliced_sprites(64, 64, 'explosion.png')
		self._images = artilleryimages
		self._frame = 0
		self.image = self._images[self._frame]
		self.rect = self.image.get_rect()
		self.dy = 5
		self.age = 0
		self.sndFire = pygame.mixer.Sound("audio\canonfire.wav")
		self.reset()
		
	def update(self):
		self.age += 1
		self.rect.centery += self.dy
		if self.age % 3 == 0:
			self._frame += 1
			self.image = self._images[self._frame]
			if self._frame >= (len(self._images) - 1):
				self.reset()
				
				
	def reset(self):
		self.rect.top = 0
		self.rect.centerx = random.randrange(0, screen.get_width())
		self.rect.centery = random.randrange(0, screen.get_height())
		self._frame = 0
		self.age = 0
		self.sndFire.play()

	def greenlight(self):
		self.dy = 0
class Cloud(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("cloud.gif")
		self.rect = self.image.get_rect()
		self.reset()

	def update(self):
		self.rect.centerx += self.dx
		self.rect.centery += self.dy
		if self.rect.top > screen.get_height():
			self.reset()
		
	def reset(self):
		self.rect.bottom = 0
		self.rect.centerx = random.randrange(0, screen.get_width())
		self.dy = random.randrange(5, 10)
		self.dx = random.randrange(-2, 2)
    		
class Ocean(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("ocean.gif")
		self.dy = 20
		self.reset()
			
	def update(self):
		self.rect.bottom += self.dy
		if self.rect.bottom >= 1440:   #1440 for x480
			self.reset() 
		
	def reset(self):
		self.rect.top = -960 #-960 for x480
		
	def greenlight(self):
		self.dy = 0

#-------------------------------------------------------------------------------
#---[ HUD Objects ]-------------------------------------------------------------
#-------------------------------------------------------------------------------
class Scoreboard(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.lives = 5
		self.score = 0
		self.distancetotarget = 5000
		self.font = pygame.font.Font("freesansbold.ttf", 20)
			
	def update(self):
		self.text = "Distance to Target: %04d       Aircraft: %d       Score: %04d" % (self.distancetotarget, self.lives, self.score)
		self.image = self.font.render(self.text, 1, (255, 255, 0))
		self.rect = self.image.get_rect()
		self.rect.left = 10
   
class NameSprite(pygame.sprite.Sprite):
	"""A sprite for the player to enter their name"""
	def __init__(self, xy):
		pygame.sprite.Sprite.__init__(self)
		self.xy = xy
		self.text = ''
		self.color = OFFWHITE
		self.font = pygame.font.Font(None, 35) # load the default font @ size 35
		self.reRender() # generate the image
	
	def addLetter(self, letter):
		"""Adds the given letter"""
		self.text += letter
		self.reRender()
	
	def removeLetter(self):
		if (len(self.text) == 1):
			self.text = ''
		else:
			self.text = self.text[:-1]
		self.reRender()
	
	def reRender(self):
		"""Updates the text"""
		self.image = self.font.render(self.text, True, self.color)
		self.rect = self.image.get_rect()
		self.rect.center = self.xy

#-------------------------------------------------------------------------------
#---[ Instructions/HighScore ]--------------------------------------------------
#-------------------------------------------------------------------------------
def display_start(level, score):
	my_font = pygame.font.Font("freesansbold.ttf", 20)
	insPlayer = "Level %d\nCumulative Score: %d\n\n" % (level, score)
	insLevelOne = "Collect as many USAF logos as possible. They are worth points!\n\n"
	insLevelTwo = "Beware the clouds because you can't see through them!\n\n"
	insLevelThree = "If you get hit by artillery fire then you lose a life. You only have 5 lives so be careful!\n\n"
	insBegin = "Left-click to being next Sortie..."
	
	my_string = insPlayer + insLevelOne
	if level == 2:
		my_string += insLevelTwo
	if level == 3:
		my_string += insLevelTwo + insLevelThree
	my_string += insBegin
	
	my_rect = pygame.Rect((20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-100))
	rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
	if rendered_text:
		screen.blit(rendered_text, my_rect.topleft)
	pygame.display.update()
	
	while (pygame.event.wait().type != pygame.MOUSEBUTTONDOWN): pass
	return

	
def display_instructions():
 	my_font = pygame.font.Font("freesansbold.ttf", 20)
	my_string = "Instructions:\nYou are an Airdrop pilot delivering needed supplies to the front line.\n\n1) Steer your C-130J using the mouse.\n2) Click once to begin the sortie.\n3) Click a second time to release the payload when you see the target.\n\nThe clouds will prevent you from seeing the ground.\nAvoid artillery fire as you can only take so many hits.\nCollect USAF logos for additional points.\n\n\nGood Luck!"
	my_rect = pygame.Rect((20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-100))
	rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
	if rendered_text:
		screen.blit(rendered_text, my_rect.topleft)
	pygame.display.update()

	return
def read_username():
	namesprite = NameSprite((SCREEN_WIDTH/2, SCREEN_HEIGHT/2-15))
	namesprites = pygame.sprite.RenderUpdates(namesprite)
	nameEntered = False
	
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	
	usrFont = pygame.font.Font("freesansbold.ttf", 35)
	color = OFFWHITE
	
	nameimage = usrFont.render('Enter Name:', True, color)
	namerect = nameimage.get_rect()
	namerect.center = 125, SCREEN_HEIGHT/2 - 15
	screen.blit(nameimage, namerect)
		
	namesprites.clear(screen, background)
	dirty = namesprites.draw(screen)
	pygame.display.update(dirty+[namerect])

	while nameEntered == False:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_BACKSPACE:
					namesprite.removeLetter()
				elif event.key == pygame.K_RETURN:
					nameEntered = True
				else:
					pressedKey = event.unicode
					try:
						# all the characters we want to follow
						if pressedKey in 'abcdefghijklmnopqrstuvwyxzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_':
							namesprite.addLetter(pressedKey)
					except:
						pass # exception from not being able to get char; don't care

		namesprites.clear(screen, background)
		dirty = namesprites.draw(screen)
		pygame.display.update(dirty+[namerect])
					
	return namesprite.text
def handle_highscores(playerscore):
	"""Called to prompt the user to enter a name for
	their score if it is high enough. then show the
	table"""
	
	# reset the screen before printing anything
	screen.blit(BLKSCREEN, (0,0))
	pygame.display.flip()
		
	
	my_font = pygame.font.Font("freesansbold.ttf", 20)
	my_rect = pygame.Rect((20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-100))
	
	highscores = parse_highscores()
	if playerscore > int(highscores[-1][1]):
		my_string = "You Scored a Total of %d points!\n\nCongratulations on making the high score list!\n\n\n" % playerscore
		rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
		if rendered_text:
			screen.blit(rendered_text, my_rect.topleft)
		pygame.display.update()

		playername = read_username()

		# sort to determine where it goes
		foundPosition = False
		for i in range(len(highscores)):
			name, score = highscores[i]
			if (playerscore > int(score)) and (foundPosition == False):
				highscores.insert(i, [str(playername), str(playerscore)])
				foundPosition = True

		highscores = highscores[0:10] # only take top 10
		
		highscorefile = 'highscores.txt'
		f = open(highscorefile, 'w')
		for name, score in highscores:
			f.write("%s:%s\n" % (name, score))
		f. close
	else:
		my_string = "You only scored a total of %d points!\n\nYou do not have a high score and you require a LOT more practice!\n\nBetter luck next time!\n\n\nClick left-mouse to continue..." % playerscore
		rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
		if rendered_text:
			screen.blit(rendered_text, my_rect.topleft)
		pygame.display.update()
		while (pygame.event.wait().type != pygame.MOUSEBUTTONDOWN) : pass
	
	
def display_highscores(scores):
	tleFont = pygame.font.Font("freesansbold.ttf", 30)
	tleFont.set_underline(True)
	color = (0, 0, 255)

	insFont = pygame.font.Font("freesansbold.ttf", 20)
	color = (255, 255, 0)
	insLabels = []
 
	title = "High Scores"
	titleimage = tleFont.render(title, True, color)
	titlerect = titleimage.get_rect()
	titlerect.centerx, titlerect.centery = SCREEN_WIDTH/2, (titlerect.height)
	screen.blit(titleimage, titlerect)

	for i in range(len(scores)):
		name, score = scores[i]
		
		# render and draw name
		nameimage = insFont.render(name, True, color)
		namerect = nameimage.get_rect()
		namerect.left, namerect.y = SCREEN_WIDTH*.2, 75+(i*(namerect.height+12))
		screen.blit(nameimage, namerect)
		
		# render and draw score
		scoreimage = insFont.render(score, True, color)
		scorerect = scoreimage.get_rect()
		scorerect.right, scorerect.y = SCREEN_WIDTH*.8, namerect.y
		screen.blit(scoreimage, scorerect)
		
		# draw dots from name to score
		for d in range (namerect.right+25, scorerect.left-10, 25):
			pygame.draw.rect(screen, color, pygame.Rect(d, scorerect.centery, 5,5))
		

	pygame.display.flip()

	return		
		
		
#-------------------------------------------------------------------------------
#---[ Game Logic ]--------------------------------------------------------------
#-------------------------------------------------------------------------------
def mainmenu():
	#Set the window caption
	pygame.display.set_caption("Welcome to Dropzone!")
			
	if not pygame.mixer:
		print "problem with sound"
	else:
		pygame.mixer.init()
		thememusic = pygame.mixer.Sound("audio\Richard_Wagner_-_Ride_of_the_Valkyries.ogg")
		thememusic.set_volume(1.0)
		thememusic.play(-1)
	
	# a surface for the dropzone game logo
	dzlogo = pygame.image.load("data\dropzone_logo450x480.png").convert()
	
	## Menu Code
	#
	menu0 = cMenu(50, 50, 20, 50, 'vertical', 100, screen,
				[('Start Game', 1, None),
				 ('Instructions', 2, None),
				 ('High Scores', 3, None),
				 ('Exit', 4, None)])
	menu0.set_position(10, 100)
	menu0.set_alignment('center', 'left')
	menu0.set_selected_color((68, 79, 162))  # set the highlighted color to match the DZ logo
	menu0.set_unselected_color(OFFWHITE)	# set not selected to OFFWHITE
	
	menu1 = cMenu(50, 50, 20, 5, 'vertical', 100, screen,
				[('Return to Main Menu', 0, None)])
	# Buffer the return-only menu to the lower-left corner
	menu1.set_position(10, SCREEN_HEIGHT-25)
	menu1.set_selected_color((68, 79, 162))  # set the highlighted color to match the DZ logo
	
	state = 0
	prev_state = 1
	rect_list = []
	
	score = 0
	while 1:
		# check if state has changed, if it has, then post a user event to
		# the queue to force the menu to be shown at least once
		if prev_state != state:
			pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key=0))
			prev_state = state
			
			# reset the screen before going to the next menu
			if state == 0:
				BLKSCREEN.blit(dzlogo, (190,0))  # add dropzone logo to the black screen
			else:
				BLKSCREEN.fill(BLACK) # clear any previously added logo
			
			screen.blit(BLKSCREEN, (0,0))
			pygame.display.flip()
		
		# Get the next event
		e = pygame.event.wait()
		
		# update the menu based on which state we are in
		if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
			if state == 0:
				rect_list, state = menu0.update(e, state)
			elif state == 1: # START GAME
				for x in range(1,4):
					display_start(x, score)
					score += rungame(x)
				#TODO: tell them their score and if they've made the high score list!
				handle_highscores(score)
				score = 0
				state = 3
			elif state == 2: # INSTRUCTIONS
				rect_list, state = menu1.update(e, state)
				display_instructions()
			elif state == 3: # HIGH SCORE
				rect_list, state = menu1.update(e, state)
				highscores = parse_highscores()
				display_highscores(highscores)
			else: # EXIT
				pygame.quit()
				sys.exit()
		if e.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		
		pygame.display.update(rect_list)

	#
	##
	
def rungame(level):
	
	# create game objects required for all levels
	ocean = Ocean()
	aircraft = Plane()
	target = Target()
	if level > 1:
		target.rect.centery = -7500
	if level > 2:
		target.rect.centery = -10000
	
	bonuspoints = USAFlogo()
	friendSprites = pygame.sprite.LayeredUpdates(ocean, bonuspoints, target, aircraft)
	
	scoreboard = Scoreboard()
	scoreSprite = pygame.sprite.Group(scoreboard)
	
	# create cloud objects when level is greater than 1
	if level > 1:
		cloud1 = Cloud()
		cloud2 = Cloud()
		cloud3 = Cloud()
		cloudSprites = pygame.sprite.Group(cloud1, cloud2, cloud3)

	# create artillery fire when level is greater than 2
	if level > 2:
		#fire1 = Artillery()
		#fire2 = Artillery()
		#fire3 = Artillery()
		#fireSprites = pygame.sprite.Group(fire1, fire2, fire3)
		fire = Artillery()
		fireSprites = pygame.sprite.Group(fire)

	
	#Create clock for sys time
	clock = pygame.time.Clock()	
	
	reachedGreenlight = False
		
	aircraft.sndEngine.play()
	
	
	keepGoing = True
	while keepGoing:
		clock.tick(30)
		pygame.mouse.set_visible(False)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT) or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
				# SPACEBAR or LEFT MOUSE CLICK will release a payload
				reachedGreenlight = True
				#call greenlight function for sprites
				#this will stop the ocean and target; make the plane keep going off-screen
				aircraft.greenlight()
				ocean.greenlight()
				target.greenlight()
				bonuspoints.greenlight()
				release_point = pygame.mouse.get_pos()
				payload = Payload(release_point)
				friendSprites.add(payload)

		if (reachedGreenlight == False) and (target.rect.centery > 500):
			reachedGreenlight = True
			aircraft.greenlight()
			ocean.greenlight()
			target.greenlight()
			bonuspoints.greenlight()
			release_point = pygame.mouse.get_pos()
			payload = Payload(release_point)
			friendSprites.add(payload)
		
		scoreboard.distancetotarget = math.hypot(target.rect.centerx - aircraft.rect.centerx, target.rect.centery - aircraft.rect.centery)
		#scoreboard.distancetotarget /= 10
		#TODO: if distance is less than 100 then set to zero and blink
		
		#check collisions				
		if aircraft.rect.colliderect(bonuspoints.rect):
			aircraft.sndMetal.play()
			bonuspoints.reset()
			scoreboard.score += 150

		if level > 1:
			hitClouds = pygame.sprite.spritecollide(aircraft, cloudSprites, False)
			#if hitClouds != []:
				#aircraft.sndThunder.play()
				#TODO: flash the screen white - for lightning sakes
		
		if level > 2:
			hitArtillery = pygame.sprite.spritecollide(aircraft, fireSprites, False)
			if hitArtillery != []:
				aircraft.sndBeenHit.play()
				scoreboard.lives -= 1
				if scoreboard.lives <= 0:
					#wait a second
					time.sleep(1.0) #sleep a sec
					#write the score to the center of the screen
					points = 0
					my_font = pygame.font.Font("freesansbold.ttf", 20)
					my_string = "You have been shot down!\n\nUSAF Points: %d\n\nAccuracy Points: %d\n\n\nTotal Points: %d" % (scoreboard.score-points, points, scoreboard.score)
					my_rect = pygame.Rect((20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-100))
					rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
					if rendered_text:
						screen.blit(background, (0,0))
						pygame.display.flip()
						screen.blit(rendered_text, my_rect.topleft)
					pygame.display.update()
					time.sleep(3.0) #sleep a sec
					#then issue a kill to the game
					keepGoing = False
				# flash the screen white
				screen.blit(WHTSCREEN, (0,0))
				pygame.display.flip()
				
				for theShell in hitArtillery:
					theShell.reset()
				
		if reachedGreenlight == True:
			if (payload.isLanded) == True:
				if payload.rect.colliderect(target.rect):
					radius = target.rect.width/2
					distance = math.hypot( payload.rect.centerx - target.rect.centerx, payload.rect.centery - target.rect.centery)
					points = radius - distance
					if points < 0: points = 0
				else:
					points = 0
				points = int(points) * 10
				scoreboard.score += points
				#wait a second
				time.sleep(1.0) #sleep a sec
				#write the score to the center of the screen
				my_font = pygame.font.Font("freesansbold.ttf", 20)
				my_string = "Level Complete!\n\nUSAF Points: %d\n\nAccuracy Points: %d\n\n\nTotal Points: %d" % (scoreboard.score-points, points, scoreboard.score)
				my_rect = pygame.Rect((20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-100))
				rendered_text = render_textrect(my_string, my_font, my_rect, OFFWHITE, (0, 0, 0), 0)
				if rendered_text:
					screen.blit(background, (0,0))
					pygame.display.flip()
					screen.blit(rendered_text, my_rect.topleft)
				pygame.display.update()
				time.sleep(3.0) #sleep a sec
				#then issue a kill to the game
				keepGoing = False
	
		if keepGoing == True:
			friendSprites.clear(screen, background)
			scoreSprite.clear(screen, background)
			if level > 1:
				cloudSprites.clear(screen, background)
			if level > 2:
				fireSprites.clear(screen, background)

			friendSprites.update()
			scoreSprite.update()
			if level > 1:
				cloudSprites.update()
			if level > 2:
				fireSprites.update()

			friendSprites.draw(screen)
			scoreSprite.draw(screen)
			if level > 1:
				cloudSprites.draw(screen)
			if level > 2:
				fireSprites.draw(screen)

			pygame.display.flip()
    
	
	aircraft.sndEngine.stop()
	# return mouse cursor
	pygame.mouse.set_visible(True)
	# black out the screen
	screen.blit(BLKSCREEN, (0, 0))
	return scoreboard.score

#-------------------------------------------------------------------------------
#---[ MAIN ]--------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == "__main__":
	mainmenu()
	
#--[ END OF FILE ]--------------------------------------------------------------
