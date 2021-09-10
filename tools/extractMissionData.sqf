diag_log text format ["START - test.sqf - [%1]", diag_tickTime]; // diag_tickTime gives insight to time spent loading config

// Configs
private _configSQM = configfile >> "X_configSQM"; // mission.sqm
private _configEXT = configfile >> "X_configEXT"; // description.ext (aka missionConfigFile)
private _version = getNumber (_configSQM >> "version");
if (_version < 53) exitWith { diag_log text format ["Error - version: %1", _version] };

// Function to write key/value pairs in json
private _fnc_json = {
	params ["_key", "_value", ["_raw", false]];
	if (_raw || {_value isEqualType 5}) exitWith {
		format ['"%1":%2', _key, _value];
	};
	if (_value isEqualType "") exitWith {
		format ['"%1":"%2"', _key, _value];
	};
	if (_value isEqualType []) exitWith {
		private _out = [format ['"%1":[', _key]];
		{
			if (_forEachIndex > 0) then { _out pushBack "," };
			_out pushBack format ['"%1"', _x];
		} forEach _value;
		_out pushBack format [']'];
		_out joinString ""
	};
	"bad type"
};

// Get all addons used
private _addons = (getArray (_configSQM >> "addons")) apply { toLower _x };

// Get all types of entities on map
private _allObjectTypes = [];
private _objectCount = 0;
private _fnc_getEntities = {
	params ["_config"];
	if (!isClass (_config >> "Entities")) exitWith {};
	private _entities = "isClass _x" configClasses (_config >> "Entities");
	{
		private _entity = _x;
		private _dataType = getText (_entity >> "dataType");
		if (_dataType == "Group") then {
			[_entity] call _fnc_getEntities;
		};
		if (_dataType == "Object" || {_dataType == "Logic"}) then {
			_objectCount = _objectCount + 1;
			_allObjectTypes pushBackUnique toLower getText (_entity >> "type");
		};
	} forEach _entities;
};
[_configSQM >> "Mission"] call _fnc_getEntities;

// Get all loadout useage
private _allLoadouts = [];
private _factions = ["potato_w", "potato_i", "potato_e", "blu_f", "ind_f", "opf_f"]; // should even support ancient missions
// for "_i" from 0 to 50 do {
// 	_factions pushBack format ["A%1",_i];
// };
{
	private _faction = _x;
	private _factionBase = _configEXT >> "CfgLoadouts" >> _faction;
	private _loadoutClasses = if (isNull _factionBase) then { [] } else { "isClass _x" configClasses _factionBase }; // ToDo: SQFVM bug on right null
	{
		private _loadoutPath = _x;
		private _loadoutName = format ["%1@%2", _faction, configName _loadoutPath];
		private _allWeapons = [];
		private _allItems = [];
		private _allAttachments = [];
		private _allMagazines = [];
		private _allBackpacks = [];
		{
			_x params ["_itemTypeAr", "_itemConfigNames"];
			{
				private _itemList = getArray (_loadoutPath >> _x);
				{
					if (_x != "") then {
						(_x splitString ":") params ["_classname"];
						_itemTypeAr pushBackUnique toLower _classname;
					};
				} forEach _itemList;
			} forEach _itemConfigNames;
		} forEach [
			[_allWeapons, ["weapons","launchers","handguns"]],
			[_allItems, ["uniform","vest","headgear","items","linkedItems"]],
			[_allAttachments, ["opticChoices", "attachments","secondaryAttachments","handgunAttachments"]],
			[_allMagazines, ["magazines", "backpackItems"]], // these could be either weapons or mags
			[_allBackpacks, ["backpack"]] // CfgVehicles, could possibly add to entities, but I think it's cleaner to leave seperate
		];

		private _loadoutInfo = [];
		_loadoutInfo pushBack (["weapons", _allWeapons] call _fnc_json);
		_loadoutInfo pushBack (["items", _allItems] call _fnc_json);
		_loadoutInfo pushBack (["attachments", _allAttachments] call _fnc_json);
		_loadoutInfo pushBack (["magazines", _allMagazines] call _fnc_json);
		_loadoutInfo pushBack (["backpacks", _allBackpacks] call _fnc_json);
		_allLoadouts pushBack ([_loadoutName, "{" + (_loadoutInfo joinString ",") + "}", true] call _fnc_json);
	} forEach _loadoutClasses;
} forEach _factions;


// assemble outuput payload
private _payloadReturn = [];
_payloadReturn pushBack (["author", getText (_configSQM >> "ScenarioData" >> "author")] call _fnc_json);
_payloadReturn pushBack (["onLoadName", getText (_configEXT >> "onLoadName")] call _fnc_json);
_payloadReturn pushBack (["bwmfDate",  getText (_configEXT >> "bwmfDate")] call _fnc_json);
_payloadReturn pushBack (["addons", _addons] call _fnc_json);
_payloadReturn pushBack (["objectCount", _objectCount] call _fnc_json);
_payloadReturn pushBack (["entities", _allObjectTypes] call _fnc_json);
_payloadReturn pushBack (["loadouts", "{" + (_allLoadouts joinString ",") + "}", true] call _fnc_json);


private _payload = "{" + (_payloadReturn joinString ",") + "}";

hint _payload;

diag_log text format ["END - test.sqf - [%1]", diag_tickTime]; // diag_tickTime gives insight to time spent executing sqf
nil
