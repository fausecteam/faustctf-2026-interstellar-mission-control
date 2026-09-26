# Interstellar Mission Control

- implemented in ~~Pascal~~ NekoVM
- cli
- based on HL7 protocol
- simulating a spaceport? i.e. inventory, crew missions etc.
- manage data stored in files/db (SQLDB)
- different commands to affect/read data
- TOC-TOU and other races need to be prevented
- parse lists of entries as Strings seperated by a special char (e.g., ';') and dont disallow that char in creation of those strings

## Structures

- Missions (Create, Finish, Abbandon, Accept, Post, Apply)
  - name (Static)
  - milestones (Static)
  - spaceship (Dynamic, Optional)
  - planets (Static)
  - deadline (Static)
  - auftraggeber (Static)
  - reward (Static)
  - overseer (Dynamic)
  - num spaceships (Static)
- Crews (Created, Update, Disband)
  - id (INTEGER)
  - name (Dynamic) (TEXT)
  - members (Dynamic, Optional) (TEXT)
  - captain (Dynamic) (INTEGER)
  - allowance (Dynamic) (INTEGER)
  - equipment (Dynamic, Optional) (TEXT)
  - (TODO: Wie tritt man bei, maybe invite code?)
- Person (Create, Update, Delete)
  - id (INTEGER)
  - authenticator (TEXT)
  - affiliation (Dynamic, Optional) (TEXT)
  - crew (Dynamic, Optional) (INTEGER)
  - name (Dynamic) (TEXT)
  - age (Static) (INTEGER)
  - dissease (Dynamic, Optional) (TEXT)
  - skills (Dynamic, Optional) (TEXT)
  - remaining lives (Dynamic) (INTEGER)
- Spaceships (Create, Delete, Update)
  - location (Dynamic)
  - fuel (Dynamic)
  - max speed (Static)
  - name (Dynamic)
  - tüv (Dynamic, Optional) (???)
  - manufacturer (Static)
  - crew (Dynamic, Optional)
  - resources (Dynamic, Optional)
  - capacity (Static)
  - mission (Dynamic, Optional)
- Ressources (Update)
  - name (Static)
  - value (Static, Optional)
  - priority (Static, Optional)
  - amount (Dyamic)
  - type (Static)
  - mass (Static)
  - special treatment (Static)
- Equipment (Create, Update, Delete)
  - name (Static)
  - user (Dynamic, Optional)
  - tüv (Dynamic, Optional)
  - type (Static)
  - mass (Static)
  - required skill (Static, Optional)
  - protection (Static, Optional)
- Planets (Discover, Update)
  - size (Static) 
  - resources (Dynamic, Optional)
  - atmosphere (Static, Optional)
  - description (Dynmic, Optional)
  - name (Static)
  - affiliation (Dynamic, Optional)
  - inabitants (Dynamic, Optional)
  - dangers (Dynamic, Optional)
- Diseases (Discover)
  - name (Static)
  - lethality (Static)
  - treatments (Static)
  - contagiousness (Static)
  - severity (Static)
- Milestones (__Create__)
  - id (INTEGER)
  - name (Static) (TEXT)
  - reward (Static) (TEXT)
  - description (Static) (TEXT)
  - requirement (Static) (TEXT)
- Spaceports (Create)
  - affiliation (Dynamic, Optional)
  - capacity (Dynamic)
  - ressources (Daynamic)
  - opening hours (Dynamic)
  - disaster help (Dynamic)
  - fees (Dynamic)
  - location (Static)

## Interface

- Register (Gibt Session-Cookie aus)
- Create
- Discover
- Update
- Delete
- Disband
- Finisch
- Abandon
- Accept
- Post
- Apply

# Templates

- Message Header (MSH):
  
  ```
  TVNI|8(<- Following Lines)|CREATE(<- Request Type (CREATE/UPDATE/DELETE/FETCH))|(<- Time(unused) ^Minutes^^Hours^^Days^^Months^^Years^)|BEING(<- Request Subject)|REQUEST(<- Message Mode (REQUEST/RESPONSE))|(Subrequests (Empty/^(Num Of Subrequests)^^(Line of Subrequest 0)^^(Line of Subrequest 1)^))
  ```

- Identity Header (IDH):
  
  ```
  SURI|id|name|auth(<- Empty at CREATE BEING Request, gets filled in by Response)
  ```

- Being Descriptor (BDR):
  
  ```
  QkRS|id|name|age|remaining_lives|affiliation|crew_id|(Empty/^NumOfDisseases^^Dissease1^^...^)|(Empty/^NumOfSkills^^Skill1^^...^)
  ```

- Crews Descriptor (CDR) 

  ```
  Q0RS|id|name|captain|allowance|(Empty/^NumOfEquipments^^Equipment1^^...^)
  ```

- Milestone Descriptor (MDR)

  ```
  TURS|id|name|(Empty/^NumOfRewards^^Reward1^^...^)|description|(Empty/^NumOfRequirements^^Req1^^...^)
  ```

- Mission Descriptor (MSD)


  ```
  TVNE|id|name|(Empty/^NumOfMilestones^^MilestoneId1^^...^)|(Empty/^SpaceshipId1^^...^)|(Empty/^NumOfPlanets^^Planet1^^...^)|deadline|sponsor|(Empty/^Reward1^^...^)|overseer

  ```

- Spaceship Descriptor (SDR)

  ```
  U0RS|id|name|^x^^y^^z^|fuel|max_speed|tuv|manufacturer|crew|(Empty/^Resources1^^...^)|capacity
  ```

- Error Descriptor (ERR)
  
  ```
  RVJS|(Code (1 for Logic/2 for Internal/))|Message
  ```


# Testing

- Working create being
```
TVNI|4|CREATE||BEING|REQUEST|
SURI||nico|
QkRS||nico|3|5|balls||No Dissease|
```

- Working create mission
```
TVNI|4|CREATE||BEING|REQUEST|
SURI||nico|auth
TVNE||name|(Empty/^NumOfMilestones^^MilestoneId1^^...^)|(Empty/^SpaceshipId1^^...^)|(Empty/^NumOfPlanets^^Planet1^^...^)|deadline|sponsor|(Empty/^Reward1^^...^)|overseer
```

# Logic

- missions accepted by crew captains
- crews only need a captain (creator)
- ships get created with crews

# Ideas

- leak data in freed chunk (z.B. namen länge selber wählen ohne zu schreiben und dann printen)

# Errors

- Null string in Milestone database in requirements (we didnt write it wtf?)
- typo where we check for auth or smth instead of request.auth

# Links
https://www.drawdb.app/editor/diagrams/3aa65853-2365-4d6e-a571-8afb8f6316e7
