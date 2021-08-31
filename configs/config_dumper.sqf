// Pseudo arma configs in json

private _output = [];
_output pushBack "{";

{
    _x params ["_base", "_condition", "_extraInfo"];
    if (_forEachIndex > 0) then { _output pushBack "," };
    _output pushBack format ['"%1": {', configName _base];
    private _classes = _condition configClasses _base;
    {
        private _config = _x;
        if (_forEachIndex > 0) then { _output pushBack "," };
        _output pushBack format ['"%1": {', toLower configName _config];
        {
            if (_forEachIndex > 0) then { _output pushBack "," };
            (_config call _x);
        } forEach _extraInfo;
        _output pushBack format ['}'];
    } forEach _classes;
    _output pushBack format [" } %1", endl];
} forEach [
    [
        configFile >> "CfgWorlds", 
        "isClass (configFile >> 'CfgWorldList' >> configName _x)", 
        [{_output pushBack format ['"description": "%1"', getText (_this >> "description")]}]
    ],
    [configFile >> "CfgPatches", "true", []],
    [
        configFile >> "CfgWeapons", 
        "(getNumber (_x >> 'scope')) > 0", 
        [
            {
                private _type = getNumber (_this >> "type");
                if (!(_type in [1,2,4])) exitWith {};
                _output pushBack format ['"compatibleMagazines": ['];
                { 
                    if (_forEachIndex > 0) then { _output pushBack "," }; 
                    _output pushBack format ['"%1"', toLower _x]; 
                } forEach ([_this] call CBA_fnc_compatibleMagazines);
		        _output pushBack ']';

                // _output pushBack format [',"compatibleItems": ['];
                // { 
                //     if (_forEachIndex > 0) then { _output pushBack "," }; 
                //     _output pushBack format ['"%1"', toLower _x]; 
                // } forEach ([configName _this] call CBA_fnc_compatibleItems);
		        // _output pushBack format [']'];
            }
        ]
    ],
    [configFile >> "CfgMagazines", "(getNumber (_x >> 'scope')) > 0", []],
    [configFile >> "CfgVehicles", "(getNumber (_x >> 'scope')) > 0", []]
];
_output pushBack "}";

x3 = _output;
count x3;
// copyToClipboard (x3 select [0, 500000] joinString "")
// copyToClipboard (x3 select [500000, 500000] joinString "")