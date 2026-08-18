import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabaseUrl = 'https://fxywkkawfsiarjpdfdvk.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testInsert() {
  const { data, error } = await supabase
    .from('orders')
    .insert({
      orderId: crypto.randomUUID(),
      paymentMethod: 'Cash',
      totalBill: 150
    })
    .select();

  if (error) {
    console.error("ERROR INSERTING INTO ORDERS:", JSON.stringify(error, null, 2));
  } else {
    console.log("SUCCESSFULLY INSERTED DATA:", data);
  }
}

testInsert();
