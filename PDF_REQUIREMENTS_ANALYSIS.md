# PDF Requirements Analysis - ASOUD Platform Shop/Office Creation

## Document Overview
- **Source**: 3-4.pdf (Persian/Farsi language)
- **Topic**: Virtual Office/Shop Creation Process in ASOUD Platform
- **Pages**: 2 pages
- **Language**: Persian (Farsi)

## 1. FUNCTIONAL REQUIREMENTS

### 1.1 Shop/Office Creation Process (Section 1.1-2.1)

#### 1.1.1 Introduction & Purpose
- **Requirement**: Platform must support virtual office/shop creation for businesses
- **Target Users**: Companies, retail shops, service businesses, and home-based businesses
- **Purpose**: Enable businesses to create virtual presence with all necessary features

#### 1.1.2 User Access Methods
- **Requirement**: Two methods for user access:
  1. **Invitation Link**: Users can join via invitation links
  2. **App Store Installation**: Users can install from app markets
- **User Type**: User 2 (specific user category)

### 1.2 Basic Information Form (Section 1.2.1)

#### 1.2.1.1 Template Selection
- **Field**: Template selection for company/shop
- **Type**: Selection field
- **Options**: Company template or Shop template
- **Requirement**: Must be selectable

#### 1.2.1.2 Business Identifier
- **Field**: Business ID/Username
- **Type**: Text input (Mandatory)
- **Validation**: 
  - Minimum 4 characters
  - English language only
  - Must be unique

#### 1.2.1.3 Business Name
- **Field**: Business/Shop name
- **Type**: Text input (Mandatory)
- **Language**: Persian/Farsi
- **Purpose**: Display name for the business

#### 1.2.1.4 Description
- **Field**: Business description
- **Type**: Text area (Optional)
- **Purpose**: Any promotional or descriptive text

#### 1.2.1.5 Business Category
- **Field**: Business category selection
- **Type**: Dropdown/Selection (Mandatory)
- **Source**: Predefined list of business categories
- **Fallback**: If desired category doesn't exist, user can request new category from ASOUD support team

### 1.3 Contact Information Form (Section 2.2.1)

#### 1.3.1 Mobile Phone
- **Field**: Mobile number
- **Type**: Phone input (Mandatory)
- **Purpose**: Customer contact (User 1 contact)
- **Validation**: Valid mobile number format

#### 1.3.2 Landline Phone
- **Field**: Fixed phone number
- **Type**: Phone input (Optional)

#### 1.3.3 Fax
- **Field**: Fax number
- **Type**: Phone input (Optional)

#### 1.3.4 Email
- **Field**: Email address
- **Type**: Email input (Optional)
- **Validation**: Valid email format

#### 1.3.5 Website
- **Field**: Website URL
- **Type**: URL input (Optional)
- **Validation**: Valid URL format

#### 1.3.6 Instagram ID
- **Field**: Instagram username
- **Type**: Text input (Optional)

#### 1.3.7 Telegram ID
- **Field**: Telegram username
- **Type**: Text input (Optional)

#### 1.3.8 Working Hours
- **Field**: Business operating hours
- **Type**: Time picker with days of week
- **Functionality**: 
  - Toggle button to enable/disable working hours
  - When enabled, shows weekday buttons
  - Can set working hours for each day
  - Days without working hours are considered closed
- **Usage**: Shared in appointment booking forms

### 1.4 Location Information Form (Section 3.2.1)

#### 1.4.1 Country
- **Field**: Country selection
- **Type**: Dropdown
- **Default**: Iran (pre-selected)

#### 1.4.2 Province/State
- **Field**: Province selection
- **Type**: Dropdown
- **Dependency**: Based on selected country

#### 1.4.3 City
- **Field**: City selection
- **Type**: Dropdown
- **Dependency**: Based on selected province

#### 1.4.4 Shop Address
- **Field**: Complete business address
- **Type**: Text area (Mandatory for User 2)
- **Purpose**: Customer visits and reference

#### 1.4.5 Postal Code
- **Field**: Postal code
- **Type**: Text input
- **Purpose**: Business location identification

#### 1.4.6 Map Location
- **Field**: Precise location on map
- **Type**: Map picker
- **Purpose**: Help customers (User 2) navigate to the shop using GPS/directions

## 2. TECHNICAL REQUIREMENTS

### 2.1 Form Navigation
- **Previous Button**: Navigate to previous form step
- **Next Button**: Navigate to next form step
- **Submit Button**: Final submission (only on last step)

### 2.2 Form Validation
- **Client-side validation**: Immediate feedback
- **Server-side validation**: Data integrity
- **Required field validation**: Prevent submission with missing mandatory fields
- **Format validation**: Email, phone, URL formats

### 2.3 Multi-step Form Process
1. **Step 1**: Basic Information (Template, ID, Name, Description, Category)
2. **Step 2**: Contact Information (Phone, Email, Social media, Working hours)
3. **Step 3**: Location Information (Country, Province, City, Address, Map)

### 2.4 Payment Gateway Integration
After shop creation, system must handle:
- **Payment Gateway Selection**: Three options provided
  1. **Personal Gateway**: User's own payment gateway (requires gateway key registration)
  2. **ASOUD Gateway**: Platform's payment gateway (requires admin approval and confirmation)
  3. **Later**: Defer payment setup
- **Subscription Payment**: After gateway selection, redirect to subscription payment
- **Discount Code**: Support for discount codes during subscription purchase

## 3. UI/UX REQUIREMENTS

### 3.1 Form Design
- **Multi-step wizard**: Clear progress indication
- **Responsive design**: Work on all devices
- **Persian/Farsi support**: RTL text direction
- **Validation feedback**: Clear error messages
- **Default values**: Pre-populate where appropriate (e.g., Iran as default country)

### 3.2 Navigation Flow
1. Main menu → Create Office/Shop icon
2. Basic Information form
3. Contact Information form  
4. Location Information form
5. Shop creation confirmation
6. Payment gateway selection
7. Subscription payment
8. Return to shop list

### 3.3 Map Integration
- **Interactive map**: For location selection
- **GPS coordinates**: Store precise location
- **Direction support**: Help customers navigate

## 4. BUSINESS LOGIC REQUIREMENTS

### 4.1 User Categories
- **User 1**: Customers/Buyers
- **User 2**: Shop owners/Business owners

### 4.2 Shop Categories
- **Companies**: Business entities
- **Retail Shops**: Product-selling businesses  
- **Service Businesses**: Service providers
- **Home-based Businesses**: Small/home operations

### 4.3 Data Completeness
- **Profile Completeness**: More complete information leads to better business presentation
- **Mandatory vs Optional**: Clear distinction between required and optional fields
- **Category Management**: Support for requesting new business categories

### 4.4 Integration Points
- **Payment Gateways**: Multiple gateway support
- **Map Services**: Location and navigation services
- **Social Media**: Instagram and Telegram integration
- **Appointment System**: Working hours integration

## 5. VALIDATION RULES

### 5.1 Business Identifier
- Minimum 4 characters
- English characters only
- Must be unique across platform

### 5.2 Contact Information
- Mobile number: Valid format and required
- Email: Valid email format if provided
- Website: Valid URL format if provided

### 5.3 Location Information
- Address: Required for User 2 (shop owners)
- Country/Province/City: Must be valid selections from provided lists
- Map location: Must be precisely selected

## 6. ERROR HANDLING

### 6.1 Form Validation Errors
- Display clear error messages for invalid inputs
- Highlight problematic fields
- Prevent form submission until all errors resolved

### 6.2 System Errors
- Handle network connectivity issues
- Graceful degradation for map services
- Backup options for payment gateway failures

## 7. SECURITY REQUIREMENTS

### 7.1 Data Protection
- Secure storage of business information
- Input sanitization to prevent injection attacks
- Proper authentication for shop creation

### 7.2 Payment Security
- Secure payment gateway integration
- PCI compliance for payment processing
- Encrypted transmission of sensitive data

## 8. PERFORMANCE REQUIREMENTS

### 8.1 Form Performance
- Fast form loading and navigation
- Responsive map interactions
- Quick validation feedback

### 8.2 Data Processing
- Efficient handling of location data
- Fast business category lookups
- Quick payment processing

This analysis covers all functional, technical, UI/UX, and business requirements extracted from the Persian PDF document.