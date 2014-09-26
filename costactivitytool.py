# Imports needed to open the DB and interact with it:
from ZODB import DB
from ZODB.FileStorage import FileStorage
from ZODB.PersistentMapping import PersistentMapping
import transaction

# Imports needed for Persistent classes:
# PersistentDict and PersistentList are ready to use as is.
# Classes you create that need to be Persistent (ZODB aware)
#     should inherit from Persistent.
from persistent import Persistent
from persistent.dict import PersistentDict
from persistent.list import PersistentList

#To exit the menu
import sys

class Product(Persistent):
	"""Models a product composition by listing the materials and activities
	needed to produce it.
	
	Attributes:
	
	Code: A key that uniquely identifies the product.
	Name: Name of the product.
	Materials: List of materials, and amounts needed to make the product.
	Activities: List of activities and its consumption needed to make the product. 
	"""

	def __init__(self, code, name, description, base_unit):
		"""Creates a new product"""
		self.code = code
		self.name = name
		self.description = description
		self.bill_of_materials = PersistentDict()
		self.bill_of_activities = PersistentDict()
		
	def addMaterial(self, material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 ):
		''' Adds a new material to the product list and the information related 
		to the consumption to the F.P. production the parameters are the following:
		material_code : Code of the material to be consumed.
		consumption: Amount of material consumed.
		consumption_unit: Unit in which the consumption amount is expressed.
		production_ratio: Units of F.P. to which the consumption is referred.
		production_unit : Unit of production to which the production ratio is related.
		waste: % of the material thrown to the waste.
		
		The function returns a Boolean and an error dictionary. If any of the parameters
		is not valid False and errors are returned. 
		'''
		
		# First of all the the information validity is checked
		
		# access material information to check code's validity
		materialtrax = MaterialTrax().materials
		# initializes a dictionary where to save the information errors.
		errors = {}
		# flag to stop saving the information if an error arises.
		information_is_valid = True
		
		if type(material_code) == int or type(material_code) == float :
			material_code =int(material_code)
			if material_code not in materialtrax:
				errors['material_code'] = "Material code does not exist"
				information_is_valid = False
		else:
			errors['material_code'] = "Material code must be an integer"
			information_is_valid = False

		if type(consumption) != float :
			errors['consumption'] = "Consumption must be a number"
			information_is_valid = False
			
		if type(production_ratio) != float :
			errors['production_ratio'] = "Production ratio must be a number"
			
		if type(waste) == float:
			if waste > 100:
				errors['waste'] = "Waste cannot be greater than 100"
				information_is_valid = False
		else:
			errors['waste'] = "Waste must be a number between 0 and 100"
			information_is_valid = False
			
		# if it is not valid it returns the errors detected so they can be 
		# corrected
		
		print information_is_valid, " antes de registrar la informacion"
		
		if information_is_valid :
			self.bill_of_materials[material_code] = {'material_code': material_code,
								'consumption': consumption,
								'consumption_unit' : consumption_unit,
								'production_unit': production_unit,
								'production_ratio': production_ratio * 1.0,
								'waste' : waste * 1.0 ,
								'cost_per_unit': cost_per_unit * 1.0}
			self._p_changed = True
			print errors
			print information_is_valid
			return True, errors
		else:		
			return False, errors
			

		
	def addActivity(self, activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0):
		"""Adds a new activity in the product list needed to make the product and
		the information related with the consumption for each unit on F.P. 
		Parameters:
		consumption: Amount of activity consumed.
		activiy_unit: Unit in which the consumption amount is expressed.
		production_ratio: Units of F.P. to which the consumption is referred.
		production_unit : Unit of production to which the production ratio is related.
		"""
		self.bill_of_activities[activity_code] = {	'activity_code': activity_code, 
											'consumption': consumption * 1.0 ,
											'activity_unit': activity_unit,
											'production_ratio': production_ratio * 1.0 ,
											'production_unit': production_unit,
											'cost_per_unit' : cost_per_unit * 1.0	}
		self._p_changed = True
		
		
	def CalculateCost(self):
		"""Calculates the direct product cost based on materials and activities consumption.
		This function doesn't check yet:
		A. Consumption units and price units for the activities are homogeneous.
		B. production ratios per unit of output are homogeneous among the activities.
		Parameters:
		Product code
		Returns two values:
			1. Total material cost.
			2. Total activity cost.
		"""
	
		 # Recovers the information about activities and materials needed to calculate the cost
		 # Maybe it would be better to filter the activities and materials in the bill of materials
		 # and bill of activities. I will implement this later if too many materials or activities
		 # are loaded in memory. One alternative is to save a reference to the material object as
		 # ZODB database works exactly as if were python objects.
		 
		activitytrax = ActivityTrax().activities
		materialtrax = MaterialTrax().materials
		
		# initialize the accum for the cost of materials and activities
		material_cost = 0
		activity_cost = 0
		
		# calculates the cost of each material and adds it to the material accum.
		# takes into account the production ratio and material waste
		for material_code, material in self.bill_of_materials.items():
			material_cost += ( 	materialtrax[material_code].cost_per_unit * 
								material["consumption"] / 
								material["production_ratio"] *
								(1 + material["waste"]/100) 
							)
		# Idem as above for activities but no waste is introduced
		for activity_code, activity in self.bill_of_activities.items():
			activity_cost += ( 	activitytrax[activity_code].cost_per_unit * 
								activity["consumption"] /
								activity["production_ratio"] 
							)
		
	
		return    material_cost , activity_cost 
		
	def PrintCost(self):
	
		material_cost, activity_cost = self.CalculateCost()
		
		total_cost = material_cost + activity_cost
		
		product_str = self.__str__()
		
		cost_str = "Product cost: {:.2f} Material's cost: {:.2f} Activity's cost: {:.2f}".format(total_cost, material_cost, activity_cost)
					
		return  product_str + cost_str + "\n"
		
	def __str__(self):
	
		materials = MaterialTrax().materials
	
		header = ("Product code: " + str(self.code) + "\nProduct name: " + self.name
				  + "\nProduct description: " + self.description + "\n" + "*" * 80 + "\n" )
				  
		material_string = "Code   Material                 Cost  Consumption  Unit       x F.P. units  Waste \n"

		for code, material in self.bill_of_materials.items():
		
			material_string += (
				str(code) + "      " +
				materials[code].name + " " * ( 25 - len(materials[code].name))  +  
				str(materials[code].cost_per_unit) + " " * (6 - len(str(materials[code].cost_per_unit))) +
				str(material["consumption"]) + " " * (13 - len(str(material["consumption"]))) +
				material["consumption_unit"] + " " * (13 - len(material["consumption_unit"])) +
				str(material["production_ratio"]) + " " +
				material["production_unit"] + "        " +
				str(material["waste"]) + "\n"
				)
				
		material_string += "*" * 80 + "\n"
		
		# will it be possible to close the materials variable once finished ? 
		# This way the memory will be emptied
		
		header += material_string	
		
		activities = ActivityTrax().activities
		
		activity_string =  "Code   Activity                Cost  Usage         Unit       x F.P. units  \n"
		
		for code, activity in self.bill_of_activities.items():
		
			activity_string += (
				str(code) + "      " +
				activities[code].name + " " * ( 25 - len(activities[code].name))  +  
				str(activities[code].cost_per_unit) + " " * (6 - len(str(activities[code].cost_per_unit))) +
				str(activity["consumption"]) + " " * (13 - len(str(activity["consumption"]))) +
				activity["activity_unit"] + " " * (13 - len(activity["activity_unit"])) +
				str(activity["production_ratio"]) + " " +
				activity["production_unit"] + "\n"
				)
		
		activity_string += "*" * 80 + "\n"
		
		header += activity_string
				
		return header
	
	
		
class Activity(Persistent):
	"""Models the activities needed to make the products and  the information
	needed to calculate its costs.
	Parameters:
	Code: Material code. It's an integer.
	Name: Material name. The name should be descriptive enough to differentiate from any other material.
	Description: Additional information that will help to describe the material.
	Cost per unit: Cost in Euros of the material according to the base unit.
	Base unit: Unit in which the material is used."""

	def __init__(self, code, name, description, cost_per_unit, activity_unit):

		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.activity_unit = activity_unit
		
	def __str__(self):

		return ("Activity Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.activity_unit))
		
		
class Material(Persistent):
	"""Models the materials used by the company to make it's products and compiles the information
	needed to calculate its costs.
	Parameters:
	Code: Material code. It's an integer.
	Name: Material name. The name should be descriptive enough to differentiate from any other material.
	Description: Additional information that will help to describe the material.
	Cost per unit: Cost in Euros of the material according to the base unit.
	Base unit: Unit in which the material is used."""
	
	def __init__(self, code, name, description, cost_per_unit, base_unit):
		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.base_unit = base_unit
	
	def __str__(self):
	
		return ("Material Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.base_unit))
		
class Trax(object):
	"""Superclass that allows to manage the company's product cost information."""

	storage = FileStorage("products.fs")
	db = DB(storage)
	connection = db.open()
	root = connection.root()

	def __init__(self, intro = "Product trax product tracking helper",
			 db_path="products.fs"):
				 
		self.intro = intro

		
class ProductTrax(Trax):
	"""Models the Company's product catalogue. If the database
	product's dictionary hasn't been created it creates it otherwise
	loads the data from the database."""

	def __init__(self, intro = "Product trax  tracking helper",
			 db_path="products.fs"):

		Trax.__init__(self)
		
		if 'products' in self.root:
			self.products = self.root['products']
		else:
			self.products = self.root['products'] = PersistentDict()


	def addProduct(self, code, name, description, base_unit):
		"""Adds a new product to the Company's catalogue. If the code is 
		already in use or is not valid returns False. If is valid returns
		True"""
		
		if not code.isdigit() or int(code) in self.products:
			return False
		
		product = Product( code, name, description, base_unit)
		self.products[code] = product
		transaction.commit()
		return True
		
	def addActivity(self, product_code, activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0):
		"""Adds a new activity to the bill of activities of an existent product. The parameters
		are the same of the Product class plus the product's code to which we add the activity"""				  
		
	
		self.products[product_code].addActivity( activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0)
						  
		transaction.commit()
		
	def addMaterial(self, product_code, material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 ):
		"""Adds a new material to the bill of materials of an existent product. The parameters
		are the same of the Product class plus the product's code to which we add the activity"""
		
		
		if product_code not in self.products:
			return False, {'code_not_catalogue':"Product code does not exist."}
		else:
			product = self.products[product_code]
			valid, errors = product.addMaterial( material_code, consumption, consumption_unit, 
							  production_ratio, production_unit,  waste, cost_per_unit= 0 )
			if valid:
				transaction.commit()
				return True, errors
			else:
				return False, errors
		
	def search(self, product_code):
		"""Returns a Product object matching the product code or false if there
		is not a product with such code"""
		if product_code not in self.products:
			return False
	
		return self.products[product_code]
		
			
			
class MaterialTrax(Trax):
	"""Models the Company's material catalogue. If the database
	material's dictionary hasn't been created it creates it otherwise
	loads the data from the database."""
		
	def __init__(self, intro = "Material trax  tracking helper",
			 db_path="products.fs"):
				 
		Trax.__init__(self)
		if 'materials' in self.root:
			self.materials = self.root['materials']
		else:
			self.materials = self.root['materials'] = PersistentDict()
		
		
	def addMaterial(self, code, name, description, cost_per_unit, base_unit):
		"""Adds a new material to the catalogue"""
		material = Material( code, name, description, cost_per_unit, base_unit)
		self.materials[code] = material
		transaction.commit()
		
	def search(self, material_code):
		"""Returns a Material object matching the material code or false if there
		is not an material with such code"""
		if material_code not in self.materials:
			return False

		return self.materials[material_code]
		
class ActivityTrax(Trax):
		
	def __init__(self, intro = "Material trax  tracking helper",
			 db_path="products.fs"):
				 
		Trax.__init__(self)
		if 'activities' in self.root:
			self.activities = self.root['activities']
		else:
			self.activities = self.root['activities'] = PersistentDict()
		
		
	def addActivity(self, code, name, description, cost_per_unit, activity_unit):
	
		activity = Activity( code, name, description, cost_per_unit, activity_unit)
		self.activities[code] = activity
		transaction.commit()
		
	def search(self, activity_code):
		"""Returns a activity object matching the activity code or false if there
		is not an activity with such code"""
		
		if activity_code not in self.activities:
			return False

		return self.activities[activity_code]
		
class Product_Menu:

	'''Display a menu respond to choices when run. '''
	def __init__(self):
		self.products = ProductTrax()
		self.choices = {
				"1": self.show_products,
				"2": self.search_product,
				"3": self.add_product,
				"3.1": self.add_material,
				"3.2": self.add_activity,
				"4": self.calculate_cost,
				"5": self.return_main,
				"6": self.quit
				}
				
	def display_menu(self):
		print(""" 
	Product's Menu
	1. Show all products
	2. Search product
	3. Add Product
	3.1. Add Material to a product
	3.2. Add Activity to a product
	4. Calculate product cost
	5. Return to the main menu
	6. Quit 
	""")
	
	def run(self):
		"""Display menu and respond to choices."""
		while True:
			self.display_menu()
			choice = str(input("Enter an option: "))
			action = self.choices.get(choice)
			if action:
				action()
			else:
				print("{0} is not a valid choice".format(choice))
				
	def show_products(self, products = None):
		if not products:
			for code, product in self.products.products.items():
				print product
					
	def search_product(self):
			
		filter = raw_input("Search for product code: ")
		
		if filter.isdigit():
			
			filter = int(filter)
			product = self.products.search(filter)
			if not product:
				print "Product code does not exist."
				answer = raw_input("Do you want to try again?(Y/N) ")
				if answer.lower() == "y":
					self.search_product()
				else:
					self.return_main()
					
			print product
			
		else: 
			
			print "The product code must be an integer. Try again. "
			self.search_product()

		
	def add_product(self):
		
		print "Enter the following product information:"
		product_data = ["Product's code", "Name", "Description", "Base unit"]
		params = []
		for data in product_data:
			memo = raw_input("Enter %s: " % (data))
			params.append(memo)
			
		if not params[0].isdigit():
			print "Product's code must be an integer. Try again."
			self.add_product()
			
		if not self.products.addProduct(*params):
			print "*" * 84
			print "Product code in use. Please enter a new code. \n"
		
	def add_material(self):
		while True:
			product_code = raw_input("Please enter product code: ").strip()
			if product_code.isdigit(): 
				product_code = int(product_code)
				if self.products.search(product_code) == False :
					answer =  raw_input("Product code does not exist. Do you want to try again(Y/N) ").strip()
					if answer == "y": continue
					else: self.return_main() 
				break
			else:
				print "Please enter a valid product code. Must be a number"
				continue
		
		while True:
		
			while True:
				material_data = [ "Material code" , "Consumption", "Consumption unit", 
								  "Production ratio", "Production unit" ,  "Waste"]
				params = [product_code]
				
				for data in material_data:
					memo = raw_input("Enter %s: " % (data)).strip()
					if memo.isdigit(): memo = float(memo)
					params.append(memo)
					
				print params
					
				valid_data, errors = self.products.addMaterial(*params)
				
				if not valid_data:
					print "The following errors must be corrected"
					for error in errors.values():
						print error, 
						
					answer = raw_input("Do you want to enter the information again?(Y/N):  ")
					if answer.lower() != "y": break
						
				break
				
			answer = raw_input("Do you want to enter another material(Y/N)? ")
			
			if answer.lower() != "y" : break
					
			
	def add_activity(self):
		activity_code = input("Please enter product code: ")
		
		while True: 
		
			material_data = [ "Activity code" , "Consumption", "Activity unit", 
							  "Output ratio", "Output unit" ]
			params = [activity_code]
			
			for data in material_data:
				memo = input("Enter %s: " % (data))
				params.append(memo)
				
			self.products.addActivity(*params)
			
			answer = str(input("Do you want to enter another material(Y/N)? "))
			
			if answer != "Y" : break	

	def calculate_cost(self):
		product_code = input("Please enter product code: ")
		
		print self.products.products[product_code].PrintCost()
		
	def return_main(self):
	
		Menu().run()
			
	def quit(self):
	
		sys.exit(0)
		
class Material_Menu:

	'''Display a menu respond to choices when run. '''
	def __init__(self):
		self.materials = MaterialTrax()
		self.choices = {
				"1": self.show_materials,
				"2": self.search_material,
				"3": self.add_material,
				"4": self.return_main,
				"5": self.quit
				}
				
	def display_menu(self):
		print(""" 
	Material's Menu
	
	1. Show all materials
	2. Search material
	3. Add material
	4. Return to main menu
	5. Quit 
	""")
	
	def run(self):
		"""Display menu and respond to choices."""
		while True:
			self.display_menu()
			choice = str(input("Enter an option: "))
			action = self.choices.get(choice)
			#print action
			if action:
				action()
			else:
				print("{0} is not a valid choice".format(choice))
				
	def show_materials(self, materials = None):
		if not materials:
			for code, material in self.materials.materials.items():
				print material
					
	def search_material(self):
		filter = input("Search for material code: ")
		material = self.materials.search(filter)
		print material
		
	def add_material(self):
		
		print "Enter the following material information:"
		material_data = ["Code", "Name", "Description","Cost per unit", "Base unit"]
		params = []
		for data in material_data:
			memo = input("Enter %s: " % (data))
			params.append(memo)
			
		self.materials.addMaterial(*params)
		
	def return_main(self):
	
		Menu().run()
		
		
	def quit(self):
	
		sys.exit(0)
			
class Activity_Menu:

	'''Display a menu respond to choices when run. '''
	def __init__(self):
		self.activities = ActivityTrax()
		self.choices = {
				"1": self.show_activities,
				"2": self.search_activity,
				"3": self.add_activity,
				"4": self.return_main,
				"5": self.quit
				}
				
	def display_menu(self):
		print(""" 
	Activity's Menu
	
	1. Show all activities
	2. Search activity
	3. Add activity
	4. Return to main menu
	5. Quit 
	""")
	
	def run(self):
		"""Display menu and respond to choices."""
		while True:
			self.display_menu()
			choice = str(input("Enter an option: "))
			action = self.choices.get(choice)
			#print action
			if action:
				action()
			else:
				print("{0} is not a valid choice".format(choice))
				
	def show_activities(self, activities = None):
		if not activities:
			for code, activity in self.activities.activities.items():
				print activity
					
	def search_activity(self):
		filter = input("Search for activity code: ")
		activity = self.activities.search(filter)
		print activity
		
	def add_activity(self):
		
		print "Enter the following activity information:"
		activity_data = ["Code", "Name", "Description","Cost per unit", "Activity unit"]
		params = []
		for data in activity_data:
			memo = input("Enter %s: " % (data))
			params.append(memo)
			
		self.activities.addActivity(*params)
		
	def return_main(self):
	
		Menu().run()
		
		
		
	def quit(self):
	
		sys.exit(0)		
		
class Menu:

	'''Display a menu respond to choices when run. '''
	def __init__(self):
		self.choices = {
				"1": self.products_menu,
				"2": self.materials_menu,
				"3": self.activities_menu,
				"4": self.quit
				}
				
	def display_menu(self):
		print(""" 
	Main Menu
	
	1. Products
	2. Materials
	3. Activities
	4. Quit 
	""")
	
	def run(self):
		"""Display menu and respond to choices."""
		while True:
			self.display_menu()
			choice = str(input("Enter an option: "))
			action = self.choices.get(choice)
			if action:
				action()
			else:
				print("{0} is not a valid choice".format(choice))
				
	def products_menu(self):
		Product_Menu().run()
					
	def materials_menu(self):
		Material_Menu().run()
		
	def activities_menu(self):
		Activity_Menu().run()
		
	def quit(self):
	
		sys.exit(0)		
		
if __name__ == '__main__':
	
	
	# materials = MaterialTrax()	
	
	# materials.addMaterial(1, "PPC 5mm 1000 gm2", "Polipropileno celular 5 mm 1000 grs / m2",100, "plancha")
	# materials.addMaterial(2, "PPC 5mm 1200 gm2", "Polipropileno celular 5 mm 1200 grs / m2",50, "plancha")
	# materials.addMaterial(3, "Perfil 5mm 1000mm", "Perfil ancho 5 mm en listones de 1000mm", 1.45, "liston")
	# materials.addMaterial(4, "Perfil 10mm 1000mm", "Perfil ancho 10 mm en listones de 1000mm", 1.45, "liston")
	# materials.addMaterial(5, "Cantonera 100mm 5+10mm", "Cantonera de 100mm de largo por lado y ancho de 5 y 10 mm", 0.45, "unidad")
	# materials.addMaterial(6, "Asas", "Asas ", 0.45, "unidad")
	# materials.addMaterial(7, "Remaches 10mm flor", "Remaches 10mm en flor ", 0.15, "unidad")	

	# for code, material in materials.materials.items():
	
		# print material
		
	# activities = ActivityTrax()
	
	# activities.addActivity(1, "Coser", "Coser", 100, "ML")
	# activities.addActivity(2, "Cortar PPC", "Cortar plancha segun medidas", 0.8, "Corte")
	# activities.addActivity(3, "Troquelar", "Cortar el perfil de la pieza usando un troquel", 1.2, "Golpe")
	# activities.addActivity(4,"Ensamblar caja", "Formar la caja, poner perfiles y cantoneras, y poner los remaches", 0.20 , "minutos")
	
	# for code, activity in activities.activities.items():
		# print activity
		
	# products = ProductTrax()
	
	# products.addProduct(1, "Caja PPC 400x600x200 mm", "Caja para tejas", "Caja")
	# products.addProduct(2, "Caja PPC 800x600x200 mm", "Caja para tejas", "Caja")
	# products.addProduct(3, "Caja PPC 1000x600x200 mm", "Caja para tejas", "Caja")
	
	# products.addMaterial(1,1, 0.5, "plancha", 1, "caja", 5)
	# products.addMaterial(1, 3, 1, "liston", 1, "caja", 5)
	# products.addMaterial(1, 4, 0.5, "liston", 1, "caja", 10)
	# products.addMaterial(1, 5, 4, "unidad", 1, "caja", 3)
	# products.addMaterial(1, 6, 2, "unidad", 1, "caja", 1)
	# products.addMaterial(1, 7, 8, "unidad", 1, "caja", 5)
	
	# products.addActivity(1 ,2 , 2, "Corte", 4 , "Caja")
	# products.addActivity(1 ,3 , 1, "Golpe", 1, "Caja")
	# products.addActivity(1 ,4 , 10, "minutos", 1, "Caja")
	

	# for code, product in products.products.items():
	
		# print product
		
	# print products.products[1].CalculateCost()
	
	# print products.products[1]
	
	
	
	# Product_Menu().run()
	
	# Material_Menu().run()
	
	# Activity_Menu().run()
	
	Menu().run()
	

	
	

	




	
	
	
	
		