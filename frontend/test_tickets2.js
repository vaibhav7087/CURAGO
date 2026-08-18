import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://fxywkkawfsiarjpdfdvk.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM';
const supabase = createClient(supabaseUrl, supabaseKey);

async function testTickets() {
  const { data, error } = await supabase
    .from('tickets')
    .select('*, patients(*)')
    .is('assignedTraineeId', null)
    .eq('ticketStatus', 'Open');

  if (error) {
    console.error("Error fetching tickets:", error.message, error.details, error.hint);
  } else {
    console.log(`Returned data length: ${data.length}`);
    console.log(JSON.stringify(data, null, 2));
  }
}

testTickets();
