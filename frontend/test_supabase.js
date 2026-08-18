import { createClient } from '@supabase/supabase-js'

const supabaseUrl = "https://fxywkkawfsiarjpdfdvk.supabase.co"
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM"

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function testConnection() {
  console.log('Testing Supabase Connection...');
  
  try {
    const { data: patients, error: patientError } = await supabase.from('patients').select('*').limit(1);
    const { data: tickets, error: ticketError } = await supabase.from('tickets').select('*').limit(1);
    const { data: inventory, error: inventoryError } = await supabase.from('inventory').select('*').limit(1);

    console.log('\n--- Connection Results ---');
    
    if (patientError) {
      console.log('Patients Table Error:', patientError.message);
    } else {
      console.log('Patients Table Readable:', true, '| Rows returned (limit 1):', patients.length, patients.length === 0 ? '(RLS might be blocking reads or table is empty)' : '');
    }

    if (ticketError) {
      console.log('Tickets Table Error:', ticketError.message);
    } else {
      console.log('Tickets Table Readable:', true, '| Rows returned (limit 1):', tickets.length, tickets.length === 0 ? '(RLS might be blocking reads or table is empty)' : '');
    }

    if (inventoryError) {
      console.log('Inventory Table Error:', inventoryError.message);
    } else {
      console.log('Inventory Table Readable:', true, '| Rows returned (limit 1):', inventory.length, inventory.length === 0 ? '(RLS might be blocking reads or table is empty)' : '');
    }
    
  } catch (error) {
    console.error('Connection Test Failed:', error);
  }
}

testConnection();
