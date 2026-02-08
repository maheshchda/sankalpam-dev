# Sankalpam Variables - Implementation Status

## ✅ Already Implemented

### 1. **Location Variables** (Current Country, State, City)
- ✅ **Status**: Fully implemented
- ✅ **Location**: `backend/app/services/template_service.py` (lines 88-105)
- ✅ **Variables Available**:
  - `{{current_location}}` - Combined city and state
  - `{{location_city}}` - Current city (translated to template language)
  - `{{location_state}}` - Current state (translated to template language)
  - `{{location_country}}` - Current country (translated to template language)
  - `{{location_city_en}}`, `{{location_state_en}}`, `{{location_country_en}}` - English versions
- ✅ **Source**: User input or reverse geocoding from coordinates
- ✅ **Service**: `backend/app/services/location_service.py` - `get_location_from_coordinates()`

### 2. **Nearby Rivers from Google Maps API**
- ✅ **Status**: Fully implemented
- ✅ **Location**: `backend/app/services/location_service.py` (lines 83-262)
- ✅ **Variables Available**:
  - `{{nearby_river}}` - Name of nearby river
  - `{{nearby_mountain}}` - Name of nearby mountain
  - `{{nearby_sea}}` - Name of nearby sea
  - `{{nearby_ocean}}` - Name of nearby ocean
  - `{{geographical_feature}}` - Primary feature (river/sea/ocean/mountain) with description
- ✅ **Priority**: Sea/Ocean > River > Mountain
- ✅ **API**: Google Places API (Nearby Search)
- ✅ **Fallback**: State-based river mapping if API fails
- ✅ **Service**: `backend/app/services/location_service.py` - `get_nearby_geographical_features()`

### 3. **User's Gotram**
- ✅ **Status**: Fully implemented
- ✅ **Location**: `backend/app/services/template_service.py` (line 79)
- ✅ **Variable Available**: `{{gotram}}` - User's gotram from profile
- ✅ **Source**: `user.gotram` from database

### 4. **Family Members**
- ✅ **Status**: Fully implemented
- ✅ **Location**: `backend/app/services/template_service.py` (lines 192-197)
- ✅ **Variables Available**:
  - `{{family_members}}` - Comma-separated list: "Name1 (Relation1), Name2 (Relation2)"
  - `{{family_members_count}}` - Number of family members
- ✅ **Source**: `FamilyMember` table filtered by `user_id`

### 5. **Occasion of Pooja (Ganesha Pooja)**
- ✅ **Status**: Fully implemented
- ✅ **Location**: `backend/app/services/template_service.py` (lines 199-203)
- ✅ **Variable Available**: `{{pooja_name}}` - Name of the pooja (e.g., "Ganesha Pooja")
- ✅ **Source**: From `PoojaSession` or request parameter

### 6. **Divine API Integration**
- ✅ **Status**: Partially implemented (structure ready, needs API endpoint configuration)
- ✅ **Location**: 
  - `backend/app/services/divineapi_panchang.py` - DivineAPI service
  - `backend/app/services/astronomical_service.py` (lines 35-62) - Integration point
- ✅ **Configuration**: `backend/app/config.py` (lines 15-20)
  - `divine_api_key` - API key
  - `divine_access_token` - Access token
  - `divineapi_base_url` - Base URL (default: "https://api.divineapi.com")
- ✅ **What's Ready**:
  - Service structure and error handling
  - Authentication (Bearer token or API key)
  - Response parsing framework
  - Integration with astronomical service
- ⚠️ **What Needs Update**:
  - Exact API endpoint URL (currently placeholder: `/v1/panchang`)
  - Request parameter format (may need adjustment)
  - Response field mapping (needs actual API response structure)
  - Authentication method (Bearer token vs API key header)

### 7. **Astronomical Variables (from Divine API or fallback)**
- ✅ **Status**: Implemented with fallback calculations
- ✅ **Location**: `backend/app/services/astronomical_service.py`
- ✅ **Variables Available**:
  - `{{samvathsarE}}` - Year name (e.g., "prabhava nAma samvathsarE")
  - `{{ayanam}}` - Solstice direction ("uttarAyaNE" or "dakshiNAyaNE")
  - `{{rithou}}` - Season (e.g., "hEmantha rithou")
  - `{{mAsE}}` - Month (e.g., "dhanur mAsE")
  - `{{pakshE}}` - Lunar phase ("shukla pakshE" or "krishna pakshE")
  - `{{thithou}}` - Lunar day (e.g., "prathamyAm shubha thithou")
  - `{{vAsara}}` - Day of week (e.g., "bhrugu vAsara")
  - `{{nakshatra}}` - Star constellation (e.g., "moolA nakshatra")
  - `{{yoga}}` - Auspicious combination (e.g., "vishkambha yoga")
  - `{{karaNa}}` - Half tithi (e.g., "bava karaNa")
  - `{{rashi}}` - Zodiac sign (e.g., "makara rAshi")
- ✅ **Priority**: DivineAPI > Fallback calculations
- ⚠️ **Note**: Fallback calculations are simplified. DivineAPI provides accurate values.

---

## 📋 Summary

### ✅ **Fully Working (No Changes Needed)**:
1. ✅ Current country, state, city
2. ✅ Nearby rivers from Google Maps API
3. ✅ User's Gotram
4. ✅ Family Members
5. ✅ Occasion of Pooja

### ⚠️ **Needs Configuration**:
6. ⚠️ Divine API - Structure is ready, but needs:
   - Actual API endpoint URL
   - Request/response format verification
   - API credentials in `.env` file

---

## 🔧 Next Steps

1. **Get Divine API Credentials**:
   - Sign up at https://developers.divineapi.com
   - Get API key or access token
   - Add to `.env`:
     ```
     Divine_API_Key=your_api_key_here
     Divine_Access_Token=your_access_token_here
     ```

2. **Test Divine API Integration**:
   - Check actual API endpoint from documentation
   - Update `divineapi_panchang.py` with correct endpoint
   - Test API call and adjust response parsing

3. **Update Template with Variables**:
   - Use variables in `TELUGU-POOJA-TEXT.md` template
   - Format: `{{variable_name}}`
   - Example: `{{location_city}}`, `{{nearby_river}}`, `{{gotram}}`, etc.

---

## 📝 Template Variable Usage Example

```telugu
శుభకరణే. {{user_name}} ({{gotram}} గోత్ర) అస్మాకం సహకుటుంబానాం ({{family_members}}) 
{{location_city}}, {{location_state}}, {{location_country}} లో {{nearby_river}} నది తీరే 
{{samvathsarE}} {{ayanam}} {{rithou}} {{mAsE}} {{pakshE}} {{thithou}} {{vAsara}} 
{{nakshatra}} {{yoga}} శుభయోగే {{pooja_name}} కరిష్యే.
```

---

## 🔍 Files to Check

1. **Template Service**: `backend/app/services/template_service.py`
2. **Location Service**: `backend/app/services/location_service.py`
3. **Astronomical Service**: `backend/app/services/astronomical_service.py`
4. **DivineAPI Service**: `backend/app/services/divineapi_panchang.py`
5. **Config**: `backend/app/config.py`
6. **Template Router**: `backend/app/routers/templates.py`

