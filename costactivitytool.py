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
		'''
		self.bill_of_materials[material_code] = {'material_code': material_code,
										'consumption': consumption,
										'consumption_unit' : consumption_unit,
										'production_unit': production_unit,
										'production_ratio': production_ratio,
										'waste' : waste,
										'cost_per_unit': cost_per_unit}
		self._p_changed = True
		
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
											'consumption': consumption,
											'activity_unit': activity_unit,
											'production_ratio': production_ratio,
											'production_unit': production_unit,
											'cost_per_unit' : cost_per_unit	}
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
		 # are loaded in memory.
		 
		activitytrax = ActivityTrax().activities
		materialtrax = MaterialTrax().materials
		 
		material_cost = 0
		activity_cost = 0
		
		for material_code, material in self.bill_of_materials.items():
			#print "Coste material : " ,  str(materialtrax[material_code].cost_per_unit), "Consumo :", 
			material_cost += ( 	materialtrax[material_code].cost_per_unit * 
								material["consumption"] / 
								material["production_ratio"] *
								(1 + material["waste"]/100) 
							)
								
		
		for activity_code, activity in self.bill_of_activities.items():
			#print "Coste activity : " ,  str(activitytrax[activity_code].cost_per_unit), "Consumo :", 
			activity_cost += ( 	activitytrax[activity_code].cost_per_unit * 
								activity["consumption"] /
								activity["production_ratio"] 
							)
		
	
		return    material_cost , activity_cost 
		
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
		
		header += material_string	
		
		activities = ActivityTrax().activities
		
		activity_string =  "Code   Activity                 Usage        Unit       x F.P. units  \n"
		
		for code, activity in self.bill_of_activities.items():
		
			activity_string += (
				str(code) + "      " +
				activities[code].name + " " * ( 25 - len(activities[code].name))  +  
				str(activity["consumption"]) + " " * (13 - len(str(activity["consumption"]))) +
				activity["activity_unit"] + " " * (13 - len(activity["activity_unit"])) +
				str(activity["production_ratio"]) + " " +
				activity["production_unit"] + "\n"
				)
		
		activity_string += "*" * 80 + "\n"
		
		header += activity_string
				
		return header
	
	
		
class Activity(Persistent):

	def __init__(self, code, name, description, cost_per_unit, activity_unit):
		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.activity_unit = activity_unit
		
	def cost_per_product(self, product, consumption):
		
		return consumption * self.cost_per_unit
		
	def __str__(self):

		return ("Activity Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.activity_unit))
		
		
class Material(Persistent):
	
	def __init__(self, code, name, description, cost_per_unit, base_unit):
		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.base_unit = base_unit
	
	def cost_per_product(self, consumption):
	
		return consumption * self.cost_per_unit
	
	def __str__(self):
	
		return ("Material Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.base_unit))
		
class Trax(object):

	storage = FileStorage("products.fs")
	db = DB(storage)
	connection = db.open()
	root = connection.root()

	def __init__(self, intro = "Product trax product tracking helper",
			 db_path="products.fs"):
				 
		self.intro = intro

		
class ProductTrax(Trax):

	def __init__(self, intro = "Product trax  tracking helper",
			 db_path="products.fs"):

		Trax.__init__(self)
		
		if 'products' in self.root:
			self.products = self.root['products']
		else:
			self.products = self.root['products'] = PersistentDict()


	def addProduct(self, code, name, description, base_unit):
		
		product = Product( code, name, description, base_unit)
		self.products[code] = product
		transaction.commit()
		
	def addActivity(self, product_code, activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0):
	
		self.products[product_code].addActivity( activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0)
						  
		transaction.commit()
		
	def addMaterial(self, product_code, material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 ):
						  
	
		self.products[product_code].addMaterial( material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 )
		transaction.commit()
		
	def list_products(self):
		print "Product			Title"
		print "=======          ====="
		for name, product in self.products.items():
			print "%-20s%s" % (name, product.description)
			
	def list_materials(self, productcode):
		print "Product: %s" % productcode
		print
		print " Material"
		print "========="
		for productcode, product in self.products[productcode].materials.items():
			print product.name
			
			
class MaterialTrax(Trax):
		
	def __init__(self, intro = "Material trax  tracking helper",
			 db_path="products.fs"):
				 
		Trax.__init__(self)
		if 'materials' in self.root:
			self.materials = self.root['materials']
		else:
			self.materials = self.root['materials'] = PersistentDict()
		
		
	def addMaterial(self, code, name, description, cost_per_unit, base_unit):
	
		material = Material( code, name, description, cost_per_unit, base_unit)
		print self.materials.items()
		self.materials[code] = material
		transaction.commit()
		
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
		
	activities = ActivityTrax()
	
	# activities.addActivity(1, "Coser", "Coser", 100, "ML")
	# activities.addActivity(2, "Cortar PPC", "Cortar plancha segun medidas", 0.8, "Corte")
	# activities.addActivity(3, "Troquelar", "Cortar el perfil de la pieza usando un troquel", 1.2, "Golpe")
	activities.addActivity(4,"Ensamblar caja", "Formar la caja, poner perfiles y cantoneras, y poner los remaches", 0.20 , "minutos")
	
	for code, activity in activities.activities.items():
		print activity
		
	products = ProductTrax()
	
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
	products.addActivity(1 ,4 , 10, "minutos", 1, "Caja")
	

	# for code, product in products.products.items():
	
		# print product
		
	print products.products[1].CalculateCost()
	
	print products.products[1]
	
	
	
	
	
	

	
	

	




	
	
	
	
		