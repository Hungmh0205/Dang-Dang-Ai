
import streamlit as st
import pandas as pd
from db_connection import get_db_manager
import time

# Page Config
st.set_page_config(
    page_title="Dang Dang AI - Admin Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB connection
@st.cache_resource
def get_db():
    try:
        return get_db_manager()
    except Exception as e:
        st.error(f"Failed to connect to DB: {e}")
        return None

db = get_db()

# Helper Functions
def run_query(query, params=None, fetch=True):
    try:
        if fetch:
            results = db.execute_query(query, params, fetch_all=True, dict_cursor=True)
            if results:
                # Results are now list of dicts with column names
                return pd.DataFrame(results)
            return pd.DataFrame()
        else:
            db.execute_query(query, params)
            return None
    except Exception as e:
        st.error(f"Query Error: {e}")
        return None

def get_table_list():
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    """
    df = run_query(query)
    if not df.empty:
        return df['table_name'].tolist()
    return []

# Sidebar
st.sidebar.title("🧠 Dang Dang Brain")
st.sidebar.markdown("---")
option = st.sidebar.radio("Navigation", ["Dashboard", "Relationship", "Data Manager", "SQL Runner"])

# --- TAB 1: DASHBOARD ---
if option == "Dashboard":
    st.title("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Validation Metric
    try:
        msg_count = run_query("SELECT COUNT(*) as count FROM messages")
        total_msgs = msg_count.iloc[0]['count'] if not msg_count.empty else 0
        
        session_count = run_query("SELECT COUNT(*) as count FROM conversation_sessions")
        total_sessions = session_count.iloc[0]['count'] if not session_count.empty else 0
        
        mem_count = run_query("SELECT COUNT(*) as count FROM episodic_memory")
        total_mems = mem_count.iloc[0]['count'] if not mem_count.empty else 0
        
        bond_df = run_query("SELECT bond, valence FROM bot_state ORDER BY id DESC LIMIT 1")
        current_bond = bond_df.iloc[0]['bond'] if not bond_df.empty else 0.5
        current_valence = bond_df.iloc[0]['valence'] if not bond_df.empty else 0.0
        
        col1.metric("Total Messages", total_msgs, delta=None)
        col2.metric("Total Sessions", total_sessions)
        col3.metric("Memories", total_mems)
        col4.metric("Bond Level", f"{current_bond:.2f}", delta=f"{current_valence:.2f} Valence")
        
    except Exception as e:
        st.error(f"Error loading metrics: {e}")

    st.markdown("### 📈 Recent Activity")
    try:
        recent_msgs = run_query("""
            SELECT role, content, timestamp, session_id 
            FROM messages 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        st.dataframe(recent_msgs, use_container_width=True)
    except Exception as e:
        st.info("No messages found.")

# --- TAB 2: DATA MANAGER ---
elif option == "Data Manager":
    st.title("🗃️ Data Manager")
    
    tables = get_table_list()
    selected_table = st.selectbox("Select Table", tables, index=0 if tables else None)
    
    if selected_table:
        # Load data
        df = run_query(f"SELECT * FROM {selected_table} ORDER BY 1 DESC LIMIT 100")
        
        st.subheader(f"Latest 100 rows in '{selected_table}'")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        # Delete functionality
        st.subheader("⚠️ Delete Row")
        row_id = st.number_input("Enter ID to delete", min_value=1, step=1)
        if st.button("Delete Row"):
            try:
                # Assuming first column is always ID
                pk_col = df.columns[0]
                run_query(f"DELETE FROM {selected_table} WHERE {pk_col} = %s", (row_id,), fetch=False)
                st.success(f"Deleted row {row_id} from {selected_table}")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {e}")

# --- TAB 3: RELATIONSHIP (V3.0) ---
elif option == "Relationship":
    st.title("❤️ Soul & Relationship Stats")
    
    st.markdown("### 🌱 Maturity Progress")
    try:
        # Get Relationship State
        state = run_query("SELECT * FROM relationship_state WHERE user_id = 'user'", fetch=True)
        if not state.empty:
            row = state.iloc[0]
            level = row['level']
            xp = row['current_xp']
            trust = row['trust_score']
            days = row['days_active']
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Level", level)
            col2.metric("XP Earned", xp)
            col3.metric("Trust Score", f"{trust:.2f}")
            col4.metric("Days Active", days)
            
            # Progress Bar (Approximate)
            base_xp = 100
            xp_needed = int(base_xp * (1.5 ** (level - 1)))
            progress = min(1.0, xp / xp_needed) if xp_needed > 0 else 0
            st.progress(progress, text=f"Progress to Lv {level + 1} ({xp}/{xp_needed} XP)")
            
        else:
            st.warning("No relationship state found. Start chatting to Initialize!")
            
    except Exception as e:
        st.error(f"Error loading stats: {e}")

    st.markdown("---")
    st.markdown("### 🧠 Core Memories (Emotional Milestones)")
    try:
        memories = run_query("SELECT * FROM core_memories ORDER BY created_at DESC", fetch=True)
        if not memories.empty:
            st.dataframe(memories, use_container_width=True)
        else:
            st.info("No core memories yet. Share a deep moment to create one!")
    except Exception as e:
        st.error(f"Error loading memories: {e}")

# --- TAB 4: SQL RUNNER ---
elif option == "SQL Runner":
    st.title("⚡ SQL Query Runner")
    st.warning("⚠️ Be careful! This executes raw SQL directly.")
    
    query = st.text_area("Enter SQL Query", height=150)
    
    if st.button("Execute"):
        if query:
            try:
                if query.strip().lower().startswith("select"):
                    df = run_query(query)
                    st.dataframe(df, use_container_width=True)
                    st.success(f"Returned {len(df)} rows")
                else:
                    run_query(query, fetch=False)
                    st.success("Query executed successfully")
            except Exception as e:
                st.error(f"Error: {e}")
