# 🌍 Dari Language Integration Guide

## Complete Dari Language Support for Electronics Store System

### 📋 **Overview**

Your electronics store inventory system now includes **complete Dari language support** with:

- **150+ UI translations** in Dari (دری)
- **Right-to-left (RTL)** text support
- **Electronics product categories** in Dari
- **Afghan cultural localization**
- **Text validation** for Dari content
- **API endpoints** for Dari integration

---

## 🚀 **Quick Setup**

### **1. Run the Setup Script**

```bash
cd electronics-store-app/backend
python setup_dari.py
```

### **2. Verify Integration**

- Start server: `python start_enhanced_server.py`
- Visit: <http://localhost:8001/docs>
- Test endpoint: `GET /languages/` (should show Dari)

---

## 🔧 **Technical Details**

### **Language Configuration**

- **Language Code**: `prs` (ISO 639-3 for Dari)
- **Native Name**: دری
- **Direction**: RTL (Right-to-left)
- **Script**: Arabic script
- **Region**: Afghanistan

### **Currency & Formatting**

- **Currency**: Afghan Afghani (AFN) ؋
- **Number Format**: ٬ (thousands), ٫ (decimal)
- **Date Format**: Persian/Solar Hijri calendar
- **Digits**: Arabic-Indic numerals (٠١٢٣٤٥٦٧٨٩)

---

## 📚 **Available Translations**

### **Core UI Elements**

```
خانه (Home)
محصولات (Products)  
موجودات (Inventory)
فروش (Sales)
مشتریان (Customers)
گزارشات (Reports)
تنظیمات (Settings)
```

### **Product Management**

```
نام محصول (Product Name)
توضیحات (Description)
قیمت (Price)
موجودی (Stock)
دسته‌بندی (Category)
برند (Brand)
گارانتی (Warranty)
```

### **Electronics Categories**

```
تلفن همراه (Mobile Phones)
کامپیوتر (Computers)
لپ‌تاپ (Laptops)
لوازم جانبی (Accessories)
شارژر (Chargers)
هدفون (Headphones)
دوربین (Cameras)
```

---

## 🔌 **API Endpoints**

### **Dari-Specific Endpoints**

#### **Setup Complete Integration**

```http
POST /languages/dari/setup
Authorization: Bearer {admin_token}
```

**Response:**

```json
{
  "success": true,
  "language_setup": {
    "language_code": "prs",
    "language_name": "Dari (دری)",
    "translations_imported": 150,
    "rtl_support": true
  },
  "categories_setup": {
    "categories_added": 10
  }
}
```

#### **Get Formatting Rules**

```http
GET /languages/dari/formatting-rules
```

**Response:**

```json
{
  "success": true,
  "formatting_rules": {
    "language_code": "prs",
    "direction": "rtl",
    "script": "Arabic",
    "currency_symbol": "؋",
    "font_recommendations": ["Noto Sans Arabic", "Tahoma"]
  }
}
```

#### **Validate Dari Text**

```http
POST /languages/dari/validate-text
Content-Type: application/json

{
  "text": "نام محصول"
}
```

#### **Add Product Categories**

```http
POST /languages/dari/add-categories
Authorization: Bearer {token}
```

### **General Multi-Language Endpoints**

#### **Get Dari Translations**

```http
GET /translations/prs
```

#### **Add Dari Translation**

```http
POST /translations/
Content-Type: application/json

{
  "language_code": "prs",
  "translation_key": "ui.welcome",
  "translation_value": "خوش آمدید",
  "context": "Welcome message"
}
```

#### **Get Localized Products**

```http
GET /products/localized/prs?limit=50&offset=0
```

---

## 🎨 **UI Implementation Guidelines**

### **CSS for RTL Support**

```css
/* RTL Layout */
.dari-layout {
  direction: rtl;
  text-align: right;
}

/* Font Stack for Dari */
.dari-text {
  font-family: 'Noto Sans Arabic', 'Arial Unicode MS', 'Tahoma', sans-serif;
  direction: rtl;
  unicode-bidi: bidi-override;
}

/* Form Elements */
.dari-form input,
.dari-form select,
.dari-form textarea {
  text-align: right;
  direction: rtl;
}

/* Navigation */
.dari-nav {
  flex-direction: row-reverse;
}
```

### **HTML Structure**

```html
<!DOCTYPE html>
<html lang="prs" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>فروشگاه الکترونیک</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic&display=swap" rel="stylesheet">
</head>
<body class="dari-layout">
  <nav class="dari-nav">
    <a href="/">خانه</a>
    <a href="/products">محصولات</a>
    <a href="/inventory">موجودات</a>
  </nav>
</body>
</html>
```

---

## 📱 **Mobile App Integration**

### **React Native RTL Support**

```javascript
import { I18nManager } from 'react-native';

// Enable RTL for Dari
if (currentLanguage === 'prs') {
  I18nManager.allowRTL(true);
  I18nManager.forceRTL(true);
}

// Text Component
<Text style={{
  fontFamily: 'NotoSansArabic',
  textAlign: 'right',
  writingDirection: 'rtl'
}}>
  {translate('product.name')}
</Text>
```

### **Translation Hook**

```javascript
const useDariTranslation = () => {
  const [translations, setTranslations] = useState({});
  
  useEffect(() => {
    fetch('/api/translations/prs')
      .then(res => res.json())
      .then(data => setTranslations(data.translations));
  }, []);
  
  const t = (key, defaultValue = key) => {
    return translations[key] || defaultValue;
  };
  
  return { t, isRTL: true };
};
```

---

## 🛠️ **Development Workflow**

### **Adding New Translations**

1. **Identify translation keys** in your code
2. **Add English version** first
3. **Add Dari translation** via API:

```bash
curl -X POST "http://localhost:8001/translations/" \
  -H "Content-Type: application/json" \
  -d '{
    "language_code": "prs",
    "translation_key": "new.feature.title",
    "translation_value": "عنوان ویژگی جدید"
  }'
```

### **Product Translation Workflow**

1. **Create product** in English
2. **Add Dari translation**:

```bash
curl -X POST "http://localhost:8001/products/translations/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 123,
    "language_code": "prs",
    "name": "گوشی هوشمند",
    "description": "گوشی هوشمند با کیفیت بالا"
  }'
```

### **Testing Dari Content**

```bash
# Validate Dari text
curl -X POST "http://localhost:8001/languages/dari/validate-text" \
  -H "Content-Type: application/json" \
  -d '{"text": "محصولات الکترونیکی"}'
```

---

## 🌟 **Best Practices**

### **Text Guidelines**

- ✅ Use **formal Dari** for business contexts
- ✅ **Right-align** all Dari text
- ✅ Use **Arabic-Indic numerals** when appropriate
- ✅ Include **cultural context** in translations
- ❌ Don't mix RTL/LTR without proper markers

### **UI/UX Guidelines**

- ✅ **Mirror layouts** for RTL
- ✅ Use **appropriate fonts** (Noto Sans Arabic recommended)
- ✅ **Test on mobile** devices
- ✅ Consider **Afghan business hours** (Sunday-Thursday)
- ❌ Don't assume left-to-right reading patterns

### **Cultural Considerations**

- 🕌 **Friday** is the weekly holiday
- 💰 **Afghan Afghani (AFN)** is the local currency
- 📅 **Solar Hijri calendar** is commonly used
- 🏪 **Business hours**: Typically 8 AM - 5 PM, Sunday-Thursday

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Text Not Displaying Correctly**

```css
/* Ensure proper font and direction */
.dari-text {
  font-family: 'Noto Sans Arabic', sans-serif;
  direction: rtl;
  unicode-bidi: embed;
}
```

#### **Layout Issues**

```css
/* Fix flexbox direction */
.dari-container {
  flex-direction: row-reverse;
}

/* Fix text alignment */
.dari-input {
  text-align: right;
}
```

#### **API Issues**

```javascript
// Check if Dari is available
fetch('/api/languages/')
  .then(res => res.json())
  .then(data => {
    const dari = data.languages.find(lang => lang.code === 'prs');
    if (!dari) {
      console.error('Dari language not found. Run setup script.');
    }
  });
```

---

## 📊 **Translation Progress**

Check translation completeness:

```http
GET /languages/translation-progress
```

**Expected Response:**

```json
{
  "success": true,
  "total_keys": 200,
  "languages": [
    {
      "code": "prs",
      "name": "Dari",
      "translated_count": 150,
      "progress_percent": 75.0
    }
  ]
}
```

---

## 🎯 **Next Steps**

### **Immediate Actions**

1. ✅ Run `python setup_dari.py`
2. ✅ Test API endpoints
3. ✅ Add product translations
4. ✅ Update UI for RTL support

### **Advanced Features**

- 📱 **Mobile app RTL** implementation
- 🎨 **Custom Dari themes**
- 📊 **Dari analytics dashboard**
- 🔍 **Dari search functionality**
- 📧 **Dari email templates**

### **Business Integration**

- 💰 **Afghan Afghani pricing**
- 📅 **Solar Hijri date picker**
- 🏪 **Local business hours**
- 📞 **Afghan phone number formats**

---

## 🎉 **Success!**

Your electronics store now supports **complete Dari language integration** with:

✅ **150+ UI translations** in professional Dari
✅ **RTL text support** for proper display
✅ **Electronics categories** in Dari
✅ **Cultural localization** for Afghanistan
✅ **API endpoints** for easy management
✅ **Text validation** for quality assurance
✅ **Mobile-ready** implementation

**Your system is now ready to serve Dari-speaking customers in Afghanistan and worldwide!** 🇦🇫

---

**Built with ❤️ for the Afghan business community**
