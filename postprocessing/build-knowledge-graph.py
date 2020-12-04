"""
File: build-knowledge-graph.py
Author: Adam Diehl
Date: 2020-12-04
Description: postprocessing script used to take the core output of the pipeline and convert it into a tabular format (CSV) that is easy to read into a graph database. 
Requirements: pandas, output of the en_full pipeline.
"""

# Packages
import pandas as pd

# Set input folder
Path = ".<PATH>" # path to folder containing en_full.cs and en.rel.cs output files from pipeline full
Label = "<LABEL>" # label to use when naming output files (i.e. <LABEL>-entities.csv, <LABEL>-events.csv, <LABEL>-relations.csv)

# Read in tab delimited data for en_full.cs
Dataframe = pd.read_csv(Path + "en_full.cs", header=None, sep='\n', skiprows=(0,1))
Dataframe = Dataframe[0].str.split('\t|\t', expand = True)
Dataframe.columns = ["ID", "Role", "Object", "Document Link", "Confidence"]

# Type confidence is in the wrong column, for these rows, move it to the appropriate column
Mask = Dataframe['Role'] == 'type'
Dataframe.loc[Mask, 'Confidence'] = Dataframe['Document Link']
Dataframe.loc[Mask, 'Document Link'] = None

#######################################
""" ENTITIES """
#######################################

print("processing entities...")

# Extract entities - filler entities not included
Entities = Dataframe[Dataframe['ID'].str.contains('Entity_EDL')]

# Distill entities DF into a 1-entity-per-row DF
EntitiesCompact = pd.DataFrame(columns=["ID", "Type", "Type Confidence", "Class", "SubClass", "SubSubClass", "Canonical Mention", "Other Mentions", "Document References", "Source Document ID", "KB Code"])

## Get ID
EntityIDs = pd.Series(Entities["ID"].unique()).str[1:] # strip leading ':'

## Get type data (ontology)
TypeMask = Entities['Role'] == 'type' 
Types = Entities.loc[TypeMask, ['ID','Object', "Confidence"]].reset_index(drop = True)
### Sometimes an entity is assigned two (or more) conflicting types. Rule: take type with highest confidence
TypesUnique = Types.sort_values(by = "Confidence", ascending=False).drop_duplicates(subset="ID", keep="first").sort_values("ID").reset_index(drop = True)
TypeLabels = TypesUnique["Object"].str.extract(r'#(.*)')
TypeLabels.columns = ["Type"]
SplitOntology = TypeLabels["Type"].str.split(".", expand=True)
SplitOntology.columns = ["Class", "SubClass", "SubSubClass"]
TypeConfidence = TypesUnique["Confidence"]

# Get canonical mentions
CanonicalMentions = Entities.loc[Entities["Role"] == 'canonical_mention', "Object"].reset_index(drop = True)
CanonicalMentions = CanonicalMentions.str.replace('\"', "") # Remove extraneous quotation marks

# Get all other mentions (and keep only unique mentions then convert to list)
OtherMentions = Entities.loc[(Entities["Role"] == 'mention') | (Entities["Role"] == 'nominal_mention') | (Entities["Role"] == 'pronominal_mention'), ["ID", "Object"]]
OtherMentions["Object"] = OtherMentions["Object"].str.replace('\"', '')
Mentions = OtherMentions.groupby("ID")["Object"].apply(set).reset_index(name="Mentions")["Mentions"].apply(list)

# Get document references
References = Entities.loc[Entities["Role"].str.contains("mention"), ["ID", "Document Link"]]
RefList = References.groupby("ID")["Document Link"].apply(set).reset_index(name="Documents")["Documents"].apply(list)
# Drop the internal coordinate
References["Document Link"] = References["Document Link"].str.split(":", expand = True)[0] 
SourceList = References.groupby("ID")["Document Link"].apply(set).reset_index(name="Documents")["Documents"].apply(list)
SourceList = SourceList.apply(", ".join)

# Get KB codes/NIL codes
KBCodes = Entities.loc[Entities["Role"] == 'link', "Object"].reset_index(drop = True)
KBCodes = KBCodes.str.extract(r'(^[^_]*)')

# Merge to master
EntitiesCompact["ID"] = EntityIDs
EntitiesCompact["Type"] = TypeLabels
EntitiesCompact["Class"] = SplitOntology["Class"]
EntitiesCompact["SubClass"] = SplitOntology["SubClass"]
EntitiesCompact["SubSubClass"] = SplitOntology["SubSubClass"]
EntitiesCompact["Type Confidence"] = TypeConfidence
EntitiesCompact["Canonical Mention"] = CanonicalMentions
EntitiesCompact["Other Mentions"] = Mentions
EntitiesCompact["Document References"] = RefList
EntitiesCompact["Source Document ID"] = SourceList
EntitiesCompact["KB Code"] = KBCodes

# Export
EntityData = EntitiesCompact.drop_duplicates(subset = "ID", keep = "first")
EntityData.to_csv("./" + Label + "-EntityList.csv", index = False)

#######################################
""" RELATIONS """
#######################################

print("processing relations...")

RelationsDF = pd.read_csv(Path + "en.rel.cs", header=None, sep='\t')
RelationsDF.columns = ["Subject", "Type", "Object", "Document", "Type Confidence"]

# Clean types
RelationsDF['Type'] = RelationsDF['Type'].str.extract(r'##(.*)')
SplitOntology = RelationsDF['Type'].str.split(".", expand = True).reset_index(drop = True)
SplitOntology.columns = ["Class", "SubClass"]
RelationsDF["Class"] = SplitOntology["Class"] 
RelationsDF["SubClass"] = SplitOntology["SubClass"]
RelationsDF = RelationsDF.drop("Type", axis = 1)

# Grab clean doc ID
SourceList = RelationsDF["Document"].str.split(":", expand = True)[0] 
RelationsDF["Source Document ID"] = SourceList

# Export
RelationsData = RelationsDF
RelationsData.to_csv("./" + Label + "-EdgeList.csv", index = False)

#######################################
""" EVENTS """
#######################################

print("processing events...")

# Extract events
Events = Dataframe[Dataframe['ID'].str.contains('Event')].reset_index(drop = True) # Events linked to entities will have EDL codes in Object column

EventsCompact = pd.DataFrame(columns = ["Event ID", "Event Type", "Canonical Mention", "Document Link"])

# Event IDs
EventIDs = pd.Series(Events["ID"].unique()).str[1:]

# Get event types - keep first because no overall type confidence
EventTypeMask = Events["Role"] == 'type'
EventTypes = Events.loc[EventTypeMask, ["ID", "Object"]].drop_duplicates(subset = "ID", keep = "first").reset_index(drop = True)
EventTypes["Object"] = EventTypes["Object"].str.extract(r'#(.*)')
EventTypes[["Class", "SubClass", "SubSubClass"]] = EventTypes["Object"].str.split(".", expand = True)

# Get actors
EventActorsMask = Events["Role"].str.contains('http')
EventActors = Events.loc[EventActorsMask, ["ID", "Role", "Object"]].reset_index(drop = True)
EventActors["Role"] = EventActors["Role"].str.extract(r'#(.*)')
EventActors["Object"] = EventActors["Object"].str[1:]
EventActors["ID"] = EventActors["ID"].str[1:]
EventActors.columns = ["Event ID", "Actor Types", "Entity IDs"]
EntityID = EventActors.groupby('Event ID')['Entity IDs'].apply(list).reset_index()
ActorTypes = EventActors.groupby('Event ID')['Actor Types'].apply(list).reset_index()
EventActors = EntityID.merge(ActorTypes, how='outer', on="Event ID")

# Canonical mentions
MentionMask = Events["Role"] == "canonical_mention.actual"
Mentions = Events.loc[MentionMask, ["ID", "Object", "Document Link"]].drop_duplicates(subset = "ID", keep = "first").reset_index(drop = True)
CanonicalMentions = Mentions["Object"].str.replace('\"', '')
DocumentLinks = Mentions["Document Link"]
SourceList = DocumentLinks.str.split(":", expand = True)[0] 

# Merge
EventsCompact["Event ID"] = EventIDs
EventsCompact["Event Type"] = EventTypes["Object"]
EventsCompact["Class"] = EventTypes["Class"]
EventsCompact["SubClass"] = EventTypes["SubClass"]
EventsCompact["SubSubClass"] = EventTypes["SubSubClass"]
EventsCompact["Canonical Mention"] = CanonicalMentions
EventsCompact["Document Link"] = DocumentLinks
EventsCompact["Source Document ID"] = SourceList
EventsCompact = EventsCompact.merge(EventActors, how='outer', on="Event ID")

# Export
EventsData = EventsCompact.drop_duplicates(subset = "Event ID", keep = "first")
EventsData.to_csv("./" + Label + "-Events.csv", index = False)


