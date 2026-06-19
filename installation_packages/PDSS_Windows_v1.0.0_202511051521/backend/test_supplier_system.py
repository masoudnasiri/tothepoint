#!/usr/bin/env python3
"""
Test script for Supplier Management System
This script tests all the supplier-related API endpoints
"""

import requests
import json
import sys
from datetime import datetime, date

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
SUPPLIERS_URL = f"{BASE_URL}/suppliers"

# Test credentials
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class SupplierTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.supplier_id = None
        self.contact_id = None
        self.document_id = None
        
    def login(self):
        """Login and get authentication token"""
        print("🔐 Logging in...")
        try:
            response = self.session.post(LOGIN_URL, json=TEST_USER)
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Login successful")
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def test_list_suppliers(self):
        """Test listing suppliers"""
        print("\n📋 Testing list suppliers...")
        try:
            response = self.session.get(SUPPLIERS_URL)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Found {data['total']} suppliers")
            if data['suppliers']:
                self.supplier_id = data['suppliers'][0]['id']
                print(f"   Using supplier ID: {self.supplier_id}")
            return True
        except Exception as e:
            print(f"❌ List suppliers failed: {e}")
            return False
    
    def test_create_supplier(self):
        """Test creating a new supplier"""
        print("\n➕ Testing create supplier...")
        supplier_data = {
            "company_name": "Test Supplier Corp",
            "legal_entity_type": "Corporation",
            "country": "Test Country",
            "city": "Test City",
            "status": "ACTIVE",
            "compliance_status": "PENDING",
            "risk_level": "MEDIUM",
            "currency_preference": "USD",
            "notes": "Test supplier created by automated test"
        }
        
        try:
            response = self.session.post(SUPPLIERS_URL, json=supplier_data)
            response.raise_for_status()
            data = response.json()
            self.supplier_id = data['id']
            print(f"✅ Supplier created with ID: {self.supplier_id}")
            print(f"   Supplier ID: {data['supplier_id']}")
            print(f"   Company: {data['company_name']}")
            return True
        except Exception as e:
            print(f"❌ Create supplier failed: {e}")
            return False
    
    def test_get_supplier(self):
        """Test getting a specific supplier"""
        if not self.supplier_id:
            print("❌ No supplier ID available for get test")
            return False
            
        print(f"\n🔍 Testing get supplier {self.supplier_id}...")
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/{self.supplier_id}")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Retrieved supplier: {data['company_name']}")
            print(f"   Status: {data['status']}")
            print(f"   Compliance: {data['compliance_status']}")
            print(f"   Risk Level: {data['risk_level']}")
            return True
        except Exception as e:
            print(f"❌ Get supplier failed: {e}")
            return False
    
    def test_update_supplier(self):
        """Test updating a supplier"""
        if not self.supplier_id:
            print("❌ No supplier ID available for update test")
            return False
            
        print(f"\n✏️ Testing update supplier {self.supplier_id}...")
        update_data = {
            "company_name": "Updated Test Supplier Corp",
            "internal_rating": 4.5,
            "notes": "Updated by automated test"
        }
        
        try:
            response = self.session.put(f"{SUPPLIERS_URL}/{self.supplier_id}", json=update_data)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Supplier updated: {data['company_name']}")
            print(f"   Rating: {data['internal_rating']}")
            return True
        except Exception as e:
            print(f"❌ Update supplier failed: {e}")
            return False
    
    def test_create_contact(self):
        """Test creating a supplier contact"""
        if not self.supplier_id:
            print("❌ No supplier ID available for contact test")
            return False
            
        print(f"\n👤 Testing create contact for supplier {self.supplier_id}...")
        contact_data = {
            "full_name": "Test Contact Person",
            "job_title": "Test Manager",
            "email": "test.contact@testsupplier.com",
            "phone": "+1-555-TEST",
            "is_primary_contact": True,
            "is_active": True,
            "notes": "Test contact created by automated test"
        }
        
        try:
            response = self.session.post(f"{SUPPLIERS_URL}/{self.supplier_id}/contacts", json=contact_data)
            response.raise_for_status()
            data = response.json()
            self.contact_id = data['id']
            print(f"✅ Contact created with ID: {self.contact_id}")
            print(f"   Name: {data['full_name']}")
            print(f"   Email: {data['email']}")
            return True
        except Exception as e:
            print(f"❌ Create contact failed: {e}")
            return False
    
    def test_list_contacts(self):
        """Test listing supplier contacts"""
        if not self.supplier_id:
            print("❌ No supplier ID available for list contacts test")
            return False
            
        print(f"\n📞 Testing list contacts for supplier {self.supplier_id}...")
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/{self.supplier_id}/contacts")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Found {data['total']} contacts")
            for contact in data['contacts']:
                print(f"   - {contact['full_name']} ({contact['email']})")
            return True
        except Exception as e:
            print(f"❌ List contacts failed: {e}")
            return False
    
    def test_utility_endpoints(self):
        """Test utility endpoints"""
        print("\n🔧 Testing utility endpoints...")
        
        # Test categories
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/categories/list")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Categories endpoint: {len(data.get('categories', []))} categories")
        except Exception as e:
            print(f"❌ Categories endpoint failed: {e}")
        
        # Test industries
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/industries/list")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Industries endpoint: {len(data.get('industries', []))} industries")
        except Exception as e:
            print(f"❌ Industries endpoint failed: {e}")
        
        # Test countries
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/countries/list")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Countries endpoint: {len(data.get('countries', []))} countries")
        except Exception as e:
            print(f"❌ Countries endpoint failed: {e}")
    
    def test_search_and_filters(self):
        """Test search and filtering functionality"""
        print("\n🔍 Testing search and filters...")
        
        # Test search
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/?search=Test")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Search 'Test': {data['total']} results")
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        # Test status filter
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/?status=ACTIVE")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Status filter 'ACTIVE': {data['total']} results")
        except Exception as e:
            print(f"❌ Status filter failed: {e}")
        
        # Test pagination
        try:
            response = self.session.get(f"{SUPPLIERS_URL}/?page=1&size=5")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Pagination: page {data['page']} of {data['pages']} ({data['total']} total)")
        except Exception as e:
            print(f"❌ Pagination failed: {e}")
    
    def cleanup(self):
        """Clean up test data"""
        if self.supplier_id:
            print(f"\n🧹 Cleaning up test supplier {self.supplier_id}...")
            try:
                response = self.session.delete(f"{SUPPLIERS_URL}/{self.supplier_id}")
                response.raise_for_status()
                print("✅ Test supplier deleted")
            except Exception as e:
                print(f"❌ Cleanup failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Supplier Management System Tests")
        print("=" * 50)
        
        # Login first
        if not self.login():
            return False
        
        # Run tests
        tests = [
            self.test_list_suppliers,
            self.test_create_supplier,
            self.test_get_supplier,
            self.test_update_supplier,
            self.test_create_contact,
            self.test_list_contacts,
            self.test_utility_endpoints,
            self.test_search_and_filters,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Supplier Management System is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the errors above.")
            return False

def main():
    """Main function"""
    tester = SupplierTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
