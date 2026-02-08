# Testing Sankalpam Generation

## ✅ Prerequisites Check

- ✅ Backend server running on http://localhost:8000
- ✅ Frontend server running on http://localhost:3000
- ✅ Divine API credentials configured in `.env`
- ✅ Google Maps API key configured

## 🧪 Test Steps

### 1. **Test Backend API Health**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Or open in browser:
http://localhost:8000/docs
```

### 2. **Test Template Generation via Frontend**

1. **Open Frontend**: http://localhost:3000
2. **Login** with your credentials
3. **Navigate to**: Generate Sankalpam page
4. **Fill in the form**:
   - Select a template (Ganesha Pooja template)
   - Enter or detect location (city, state, country)
   - Click "Get Current Location" or enter coordinates
5. **Click "Generate Sankalpam"**

### 3. **Verify Variables Are Populated**

The generated Sankalpam should include:
- ✅ **Location**: City, State, Country
- ✅ **Nearby River**: From Google Maps API
- ✅ **Gotram**: From user profile
- ✅ **Family Members**: From family members list
- ✅ **Pooja Name**: "Ganesha Pooja" or selected pooja
- ✅ **Astronomical Data**: 
  - Year (samvathsarE)
  - Season (rithou)
  - Month (mAsE)
  - Tithi (thithou) - from Divine API
  - Nakshatra - from Divine API
  - Yoga - from Divine API
  - Day of week (vAsara)

### 4. **Test Divine API Integration**

Check backend logs to see if Divine API is being called:
- Look for: "Calling DivineAPI Panchang: ..."
- Check response: "DivineAPI Panchang response: ..."

If Divine API fails, it will fall back to approximate calculations.

### 5. **Test Google Maps API for Rivers**

When you provide coordinates:
- Backend should call Google Places API
- Should find nearby rivers/water bodies
- Should populate `{{nearby_river}}` variable

## 🔍 Debugging

### Check Backend Logs
Look at the terminal running `uvicorn main:app --reload` for:
- Divine API calls
- Google Maps API calls
- Variable replacement logs
- Any errors

### Check Frontend Console
Open browser DevTools (F12) and check:
- Network tab for API calls
- Console for any errors
- Response data from `/api/templates/generate`

### Common Issues

1. **Divine API not working**:
   - Check `.env` file has correct credentials
   - Restart backend server after adding credentials
   - Check API endpoint URL in `divineapi_panchang.py`

2. **Google Maps API not finding rivers**:
   - Verify API key is correct
   - Check if location has nearby rivers
   - Check API quota/limits

3. **Variables not replacing**:
   - Check template text has `{{variable_name}}` format
   - Verify user has gotram in profile
   - Check family members are added

## 📝 Expected Template Variables

Your template should use these variables:

```telugu
శుభకరణే. {{user_name}} ({{gotram}} గోత్ర) అస్మాకం సహకుటుంబానాం ({{family_members}}) 
{{location_city}}, {{location_state}}, {{location_country}} లో {{nearby_river}} నది తీరే 
{{samvathsarE}} {{ayanam}} {{rithou}} {{mAsE}} {{pakshE}} {{thithou}} {{vAsara}} 
{{nakshatra}} {{yoga}} శుభయోగే {{pooja_name}} కరిష్యే.
```

## ✅ Success Criteria

- [ ] Backend responds to health check
- [ ] Frontend loads and user can login
- [ ] Template selection works
- [ ] Location detection works (coordinates → city/state/country)
- [ ] Nearby river is found via Google Maps API
- [ ] Divine API provides tithi, nakshatra, yoga (or fallback works)
- [ ] All variables are replaced in generated Sankalpam
- [ ] Audio is generated and plays correctly

## 🚀 Quick Test Command

```bash
# Test backend
curl http://localhost:8000/health

# Test with sample data (requires authentication token)
# Use the frontend UI for full testing
```

