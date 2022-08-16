import cript
from getpass import getpass
import requests
import os
import pandas as pd
import json
import yaml

def load_config():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    if config.get("host") is None:
        config["host"] = input("Host (e.g., criptapp.org): ")
    if config.get("token") is None:
        config["token"] = getpass("API Token: ")
    if config.get("group") is None:
        config["group"] = input("Group name: ")
    if config.get("project") is None:
        config["project"] = input("Project name: ")
    if config.get("collection") is None:
        config["collection"] = input("Collection name: ")
    if config.get("inventory") is None:
        config["inventory"] = input("Inventory name: ")
    if config.get("public") is None:
        # Prompt user for privacy setting
        config["public"] = input("Do you want your data visible to the public? (y/N): ").lower() == "y"
    if config.get("path") is None:
        config["path"] = input("Path to CSV file: ").strip('"')

    return config

def get_inventory(inventory_name, group, collection, api, public):
    """Either creates or retrieves an inventory object from CRIPT.
    @args:
    inventory_name:string
    group:cript group object
    collection:cript collection object
    api:cript api object
    public:boolean

    @return:cript inventory object
    """

    inventory = cript.Inventory(group=group, collection=collection, name=inventory_name, materials=[], public=public)

    # Save inventory or fetch and update existing inventory
    api.save(inventory,update_existing=True, max_level=0)
    

    return inventory

def get_polymer(index,row,api,group,project,public):
    """Creates or receives a cript Material object.
    @args:
    index: int
    row: pandas DataSeries
    api: cript api object
    group: cript group object
    public: boolean
    @return: cript material object
    """

    #Creates polymer name from the monomers that comprise it
    mono1_name=row["name1"]
    mono2_name=row["name2"]
    poly_name=f'{mono1_name}-db-{mono2_name}_({str(index+1)})'

    #Create identifier objects for polymer
    idpol=[cript.Identifier(key="preferred_name", value=poly_name),
    cript.Identifier(key="bigsmiles", value=row["BIGSMILES"])]
    
    notes={}

    mono1_info={"name":mono1_name,
    "N":row["N1"],
    "v(nm3)":row["v1(nm3)"],
    "Rg(nm)":row["Rg1(nm)"]}

    mono2_info={"name":mono2_name,
    "N":row["N1"],
    "v(nm3)":row["v2(nm3)"],
    "Rg(nm)":row["Rg2(nm)"]}

    other_info={"Lapprox":row["Lapprox"],
    "nchains":row["nchains"],
    "Vbox(nm3)":row["Vbox(nm3)"],
    "T(K)":row["T(K)"],
    "chi(vref=0.1nm3)":row["chi(vref=0.1nm3)"],
    "chistd":row["chistd"],
    "directory":row["directory"]
    }

    notes={"component1":mono1_info, "component2":mono2_info}
    notes.update(other_info)
    notes=json.dumps(notes)
    

    poly_dict={"group": group,
    "project":project,
    "name": poly_name,
    "identifiers": idpol,
    "notes": notes,
    "public": public}

    polymer = cript.Material(**poly_dict)

    # Save material or fetch and update existing
    
    api.save(polymer,update_existing = True, max_level=0)
    

    return polymer

def parseFile(path,inventory,group,project,api,public):
    """Iterates through rows and calls upon get_polymer to make material objects.
    Adds materials to specified inventory.
    @args:
    path: str, file path
    inventory:cript inventory object
    group: cript group object
    api:cript api object
    public:boolean
    @return: None
    """
    df=pd.read_csv(path)
    
    for index,row in df.iterrows():
        polymer=get_polymer(index,row,api,group,project,public)
        inventory.materials.append(polymer)

    api.save(inventory, max_level=0)


        
        



       
        



if __name__ == "__main__":
    
    config=load_config()
    # Establish connection with the API
    api = cript.API(config["host"], config["token"])

    # Fetch objects
    group = api.get(cript.Group, {"name": config["group"]}, max_level=0)
    project = api.get(cript.Project, {"name":config["project"]}, max_level=0)
    collection = api.get(cript.Collection, {"name": config["collection"], "group": group.uid, "project": project.uid}, max_level=0)

    inventory=get_inventory(
        config["inventory"],
        group,
        collection,
        api,
        config["public"]
        )

    parseFile(config["path"],inventory,group,project,api,config["public"])
    print("Upload completed")
