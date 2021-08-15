
private _output = [];
_output pushBack "{";

{
    _x params ["_base", "_condition", "_getExtra"];
    if (_forEachIndex > 0) then { _output pushBack "," };
    _output pushBack format ['"%1": {', configName _base];
    private _classes = _condition configClasses _base;
    {
        if (_forEachIndex > 0) then { _output pushBack "," };
        private _extra = _x call _getExtra;
        _output pushBack format ['"%1": {%2}', toLower configName _x, _extra];
    } forEach _classes;
    _output pushBack format [" } %1", endl];
} forEach [
    [
        configFile >> "CfgWorlds", 
        "isClass (configFile >> 'CfgWorldList' >> configName _x)", 
        {format ['"description": "%1"', getText (_this >> "description")]}
    ],
    [configFile >> "CfgPatches", "true", {""}],
    [configFile >> "CfgWeapons", "(getNumber (_x >> 'scope')) > 0", {""}],
    [configFile >> "CfgMagazines", "(getNumber (_x >> 'scope')) > 0", {""}],
    [configFile >> "CfgVehicles", "(getNumber (_x >> 'scope')) > 0", {""}]
];
_output pushBack "}";

copyToClipboard (_output joinString "");
