--
-- PostgreSQL database dump
--

\restrict 01Jj6bA0CjbIPRjgeeCLcWjFn6bsc53dugbYT6uFj3bcH7ya7Qc4XjdKbbmtHCu

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: projectitemstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.projectitemstatus AS ENUM (
    'PENDING',
    'SUGGESTED',
    'DECIDED',
    'PROCURED',
    'FULFILLED',
    'PAID',
    'CASH_RECEIVED'
);


ALTER TYPE public.projectitemstatus OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: budget_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.budget_data (
    id integer NOT NULL,
    budget_date date NOT NULL,
    available_budget numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.budget_data OWNER TO postgres;

--
-- Name: budget_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.budget_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.budget_data_id_seq OWNER TO postgres;

--
-- Name: budget_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.budget_data_id_seq OWNED BY public.budget_data.id;


--
-- Name: cashflow_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cashflow_events (
    id integer NOT NULL,
    related_decision_id integer,
    event_type character varying(10) NOT NULL,
    forecast_type character varying(10) NOT NULL,
    event_date date NOT NULL,
    amount numeric(15,2) NOT NULL,
    description text,
    is_cancelled boolean NOT NULL,
    cancelled_at timestamp with time zone,
    cancelled_by_id integer,
    cancellation_reason text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cashflow_events OWNER TO postgres;

--
-- Name: cashflow_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cashflow_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cashflow_events_id_seq OWNER TO postgres;

--
-- Name: cashflow_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cashflow_events_id_seq OWNED BY public.cashflow_events.id;


--
-- Name: decision_factor_weights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.decision_factor_weights (
    id integer NOT NULL,
    factor_name character varying(100) NOT NULL,
    weight integer NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT check_weight_range CHECK (((weight >= 1) AND (weight <= 10)))
);


ALTER TABLE public.decision_factor_weights OWNER TO postgres;

--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.decision_factor_weights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.decision_factor_weights_id_seq OWNER TO postgres;

--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.decision_factor_weights_id_seq OWNED BY public.decision_factor_weights.id;


--
-- Name: delivery_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.delivery_options (
    id integer NOT NULL,
    project_item_id integer NOT NULL,
    delivery_slot integer,
    delivery_date date NOT NULL,
    invoice_timing_type character varying(20) NOT NULL,
    invoice_issue_date date,
    invoice_days_after_delivery integer,
    invoice_amount_per_unit numeric(12,2) NOT NULL,
    preference_rank integer,
    notes text,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.delivery_options OWNER TO postgres;

--
-- Name: delivery_options_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.delivery_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.delivery_options_id_seq OWNER TO postgres;

--
-- Name: delivery_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.delivery_options_id_seq OWNED BY public.delivery_options.id;


--
-- Name: finalized_decisions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.finalized_decisions (
    id integer NOT NULL,
    run_id uuid,
    project_id integer NOT NULL,
    project_item_id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    procurement_option_id integer NOT NULL,
    purchase_date date NOT NULL,
    delivery_date date NOT NULL,
    quantity integer NOT NULL,
    final_cost numeric(12,2) NOT NULL,
    status character varying(20) NOT NULL,
    delivery_option_id integer,
    forecast_invoice_timing_type character varying(20) NOT NULL,
    forecast_invoice_issue_date date,
    forecast_invoice_days_after_delivery integer,
    forecast_invoice_amount numeric(12,2),
    actual_invoice_issue_date date,
    actual_invoice_amount numeric(12,2),
    actual_invoice_received_date date,
    invoice_entered_by_id integer,
    invoice_entered_at timestamp with time zone,
    decision_maker_id integer NOT NULL,
    decision_date timestamp with time zone NOT NULL,
    finalized_at timestamp with time zone,
    finalized_by_id integer,
    is_manual_edit boolean,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.finalized_decisions OWNER TO postgres;

--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.finalized_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.finalized_decisions_id_seq OWNER TO postgres;

--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.finalized_decisions_id_seq OWNED BY public.finalized_decisions.id;


--
-- Name: optimization_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.optimization_results (
    id integer NOT NULL,
    run_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now(),
    project_id integer,
    item_code character varying(50) NOT NULL,
    procurement_option_id integer NOT NULL,
    purchase_time integer NOT NULL,
    delivery_time integer NOT NULL,
    quantity integer NOT NULL,
    final_cost numeric(12,2) NOT NULL
);


ALTER TABLE public.optimization_results OWNER TO postgres;

--
-- Name: optimization_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.optimization_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.optimization_results_id_seq OWNER TO postgres;

--
-- Name: optimization_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.optimization_results_id_seq OWNED BY public.optimization_results.id;


--
-- Name: optimization_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.optimization_runs (
    run_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now(),
    request_parameters json NOT NULL,
    status character varying(20) NOT NULL
);


ALTER TABLE public.optimization_runs OWNER TO postgres;

--
-- Name: procurement_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.procurement_options (
    id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    supplier_name text NOT NULL,
    base_cost numeric(12,2) NOT NULL,
    lomc_lead_time integer,
    discount_bundle_threshold integer,
    discount_bundle_percent numeric(5,2),
    payment_terms json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    is_active boolean
);


ALTER TABLE public.procurement_options OWNER TO postgres;

--
-- Name: procurement_options_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.procurement_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.procurement_options_id_seq OWNER TO postgres;

--
-- Name: procurement_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.procurement_options_id_seq OWNED BY public.procurement_options.id;


--
-- Name: project_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_assignments (
    user_id integer NOT NULL,
    project_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.project_assignments OWNER TO postgres;

--
-- Name: project_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_items (
    id integer NOT NULL,
    project_id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    item_name text,
    quantity integer NOT NULL,
    delivery_options json NOT NULL,
    status public.projectitemstatus NOT NULL,
    external_purchase boolean,
    decision_date date,
    procurement_date date,
    payment_date date,
    invoice_submission_date date,
    expected_cash_in_date date,
    actual_cash_in_date date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.project_items OWNER TO postgres;

--
-- Name: project_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.project_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_items_id_seq OWNER TO postgres;

--
-- Name: project_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.project_items_id_seq OWNED BY public.project_items.id;


--
-- Name: project_phases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_phases (
    id integer NOT NULL,
    project_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.project_phases OWNER TO postgres;

--
-- Name: project_phases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.project_phases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_phases_id_seq OWNER TO postgres;

--
-- Name: project_phases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.project_phases_id_seq OWNED BY public.project_phases.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    project_code character varying(50) NOT NULL,
    name text NOT NULL,
    priority_weight integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean,
    CONSTRAINT check_priority_weight_range CHECK (((priority_weight >= 1) AND (priority_weight <= 10)))
);


ALTER TABLE public.projects OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: budget_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_data ALTER COLUMN id SET DEFAULT nextval('public.budget_data_id_seq'::regclass);


--
-- Name: cashflow_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events ALTER COLUMN id SET DEFAULT nextval('public.cashflow_events_id_seq'::regclass);


--
-- Name: decision_factor_weights id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights ALTER COLUMN id SET DEFAULT nextval('public.decision_factor_weights_id_seq'::regclass);


--
-- Name: delivery_options id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options ALTER COLUMN id SET DEFAULT nextval('public.delivery_options_id_seq'::regclass);


--
-- Name: finalized_decisions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions ALTER COLUMN id SET DEFAULT nextval('public.finalized_decisions_id_seq'::regclass);


--
-- Name: optimization_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results ALTER COLUMN id SET DEFAULT nextval('public.optimization_results_id_seq'::regclass);


--
-- Name: procurement_options id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_options ALTER COLUMN id SET DEFAULT nextval('public.procurement_options_id_seq'::regclass);


--
-- Name: project_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items ALTER COLUMN id SET DEFAULT nextval('public.project_items_id_seq'::regclass);


--
-- Name: project_phases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases ALTER COLUMN id SET DEFAULT nextval('public.project_phases_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: budget_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.budget_data (id, budget_date, available_budget, created_at, updated_at) FROM stdin;
313	2025-01-01	50000.00	2025-10-09 13:28:59.405201+00	\N
314	2025-01-31	75000.00	2025-10-09 13:28:59.405201+00	\N
315	2025-03-02	100000.00	2025-10-09 13:28:59.405201+00	\N
316	2025-04-01	125000.00	2025-10-09 13:28:59.405201+00	\N
317	2025-05-01	150000.00	2025-10-09 13:28:59.405201+00	\N
318	2025-05-31	175000.00	2025-10-09 13:28:59.405201+00	\N
319	2025-06-30	200000.00	2025-10-09 13:28:59.405201+00	\N
320	2025-07-30	225000.00	2025-10-09 13:28:59.405201+00	\N
321	2025-08-29	250000.00	2025-10-09 13:28:59.405201+00	\N
322	2025-09-28	275000.00	2025-10-09 13:28:59.405201+00	\N
323	2025-10-28	300000.00	2025-10-09 13:28:59.405201+00	\N
324	2025-11-27	325000.00	2025-10-09 13:28:59.405201+00	\N
\.


--
-- Data for Name: cashflow_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cashflow_events (id, related_decision_id, event_type, forecast_type, event_date, amount, description, is_cancelled, cancelled_at, cancelled_by_id, cancellation_reason, created_at) FROM stdin;
\.


--
-- Data for Name: decision_factor_weights; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.decision_factor_weights (id, factor_name, weight, description, created_at, updated_at) FROM stdin;
209	cost_minimization	9	Prioritize minimizing total procurement cost	2025-10-09 13:28:59.410155+00	\N
210	lead_time_optimization	8	Optimize delivery times to meet project deadlines	2025-10-09 13:28:59.410155+00	\N
211	supplier_rating	7	Consider supplier reliability and quality ratings	2025-10-09 13:28:59.410155+00	\N
212	cash_flow_balance	8	Balance cash outflows across time periods	2025-10-09 13:28:59.410155+00	\N
213	bundle_discount_maximization	6	Maximize bulk purchase discounts when possible	2025-10-09 13:28:59.410155+00	\N
214	quality_assurance	7	Ensure high-quality materials and workmanship	2025-10-09 13:28:59.410155+00	\N
215	risk_mitigation	6	Minimize procurement and delivery risks	2025-10-09 13:28:59.410155+00	\N
216	sustainability	5	Prefer environmentally friendly options	2025-10-09 13:28:59.410155+00	\N
\.


--
-- Data for Name: delivery_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.delivery_options (id, project_item_id, delivery_slot, delivery_date, invoice_timing_type, invoice_issue_date, invoice_days_after_delivery, invoice_amount_per_unit, preference_rank, notes, is_active, created_at, updated_at) FROM stdin;
2601	1301	1	2025-04-23	RELATIVE	2025-06-10	48	111.79	1	Delivery option 1 for Security Cameras - IP Network	t	2025-10-09 13:28:59.389009+00	\N
2602	1301	2	2025-05-01	RELATIVE	2025-07-24	84	168.45	2	Delivery option 2 for Security Cameras - IP Network	t	2025-10-09 13:28:59.389009+00	\N
2603	1302	1	2025-03-28	RELATIVE	2025-05-11	44	144.42	1	Delivery option 1 for Acoustic Insulation - Fiberglass	t	2025-10-09 13:28:59.389009+00	\N
2604	1302	2	2025-04-12	RELATIVE	2025-06-16	65	135.16	2	Delivery option 2 for Acoustic Insulation - Fiberglass	t	2025-10-09 13:28:59.389009+00	\N
2605	1303	1	2025-03-11	RELATIVE	2025-04-14	34	165.81	1	Delivery option 1 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2606	1303	2	2025-03-31	RELATIVE	2025-06-12	73	94.07	2	Delivery option 2 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2607	1304	1	2025-03-23	RELATIVE	2025-04-28	36	126.72	1	Delivery option 1 for Electrical Cables - 3-Core 2.5mm²	t	2025-10-09 13:28:59.389009+00	\N
2608	1304	2	2025-04-04	RELATIVE	2025-06-14	71	161.22	2	Delivery option 2 for Electrical Cables - 3-Core 2.5mm²	t	2025-10-09 13:28:59.389009+00	\N
2609	1305	1	2025-04-04	RELATIVE	2025-05-13	39	164.86	1	Delivery option 1 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2610	1305	2	2025-04-18	RELATIVE	2025-06-05	48	130.95	2	Delivery option 2 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2611	1306	1	2025-05-05	RELATIVE	2025-07-18	74	95.41	1	Delivery option 1 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
2612	1306	2	2025-05-13	RELATIVE	2025-07-08	56	113.30	2	Delivery option 2 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
2613	1307	1	2025-05-29	RELATIVE	2025-07-19	51	91.64	1	Delivery option 1 for Computer Equipment - Desktop	t	2025-10-09 13:28:59.389009+00	\N
2614	1307	2	2025-06-17	RELATIVE	2025-08-28	72	147.38	2	Delivery option 2 for Computer Equipment - Desktop	t	2025-10-09 13:28:59.389009+00	\N
2615	1308	1	2025-04-15	RELATIVE	2025-06-02	48	139.37	1	Delivery option 1 for Structural Steel Beams - H-Beam 200x200mm	t	2025-10-09 13:28:59.389009+00	\N
2616	1308	2	2025-04-29	RELATIVE	2025-07-03	65	114.40	2	Delivery option 2 for Structural Steel Beams - H-Beam 200x200mm	t	2025-10-09 13:28:59.389009+00	\N
2617	1309	1	2025-05-24	RELATIVE	2025-08-05	73	162.02	1	Delivery option 1 for Personal Protective Equipment Set	t	2025-10-09 13:28:59.389009+00	\N
2618	1309	2	2025-06-07	RELATIVE	2025-08-11	65	104.77	2	Delivery option 2 for Personal Protective Equipment Set	t	2025-10-09 13:28:59.389009+00	\N
2619	1310	1	2025-03-12	RELATIVE	2025-06-05	85	161.67	1	Delivery option 1 for Landscaping - Trees & Shrubs	t	2025-10-09 13:28:59.389009+00	\N
2620	1310	2	2025-03-24	RELATIVE	2025-06-17	85	156.92	2	Delivery option 2 for Landscaping - Trees & Shrubs	t	2025-10-09 13:28:59.389009+00	\N
2621	1311	1	2025-03-09	RELATIVE	2025-05-12	64	96.23	1	Delivery option 1 for Parking Bollards - Concrete	t	2025-10-09 13:28:59.389009+00	\N
2622	1311	2	2025-03-18	RELATIVE	2025-05-04	47	89.61	2	Delivery option 2 for Parking Bollards - Concrete	t	2025-10-09 13:28:59.389009+00	\N
2623	1312	1	2025-03-20	RELATIVE	2025-04-23	34	108.60	1	Delivery option 1 for Interior Paint - Low VOC	t	2025-10-09 13:28:59.389009+00	\N
2624	1312	2	2025-04-01	RELATIVE	2025-05-24	53	116.55	2	Delivery option 2 for Interior Paint - Low VOC	t	2025-10-09 13:28:59.389009+00	\N
2625	1313	1	2025-03-12	RELATIVE	2025-04-21	40	120.34	1	Delivery option 1 for Concrete Mixer - 3m³	t	2025-10-09 13:28:59.389009+00	\N
2626	1313	2	2025-03-23	RELATIVE	2025-05-12	50	159.92	2	Delivery option 2 for Concrete Mixer - 3m³	t	2025-10-09 13:28:59.389009+00	\N
2627	1314	1	2025-05-16	RELATIVE	2025-07-14	59	102.87	1	Delivery option 1 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2628	1314	2	2025-05-30	RELATIVE	2025-07-13	44	95.80	2	Delivery option 2 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2629	1315	1	2025-03-23	RELATIVE	2025-05-09	47	128.23	1	Delivery option 1 for Formwork - Plywood Sheets	t	2025-10-09 13:28:59.389009+00	\N
2630	1315	2	2025-04-03	RELATIVE	2025-06-30	88	165.66	2	Delivery option 2 for Formwork - Plywood Sheets	t	2025-10-09 13:28:59.389009+00	\N
2631	1316	1	2025-03-07	RELATIVE	2025-04-13	37	154.81	1	Delivery option 1 for Thermal Insulation - Rockwool	t	2025-10-09 13:28:59.389009+00	\N
2632	1316	2	2025-03-27	RELATIVE	2025-06-07	72	112.88	2	Delivery option 2 for Thermal Insulation - Rockwool	t	2025-10-09 13:28:59.389009+00	\N
2633	1317	1	2025-05-29	RELATIVE	2025-07-04	36	119.19	1	Delivery option 1 for Air Conditioning Units - Split Type	t	2025-10-09 13:28:59.389009+00	\N
2634	1317	2	2025-06-12	RELATIVE	2025-07-15	33	152.83	2	Delivery option 2 for Air Conditioning Units - Split Type	t	2025-10-09 13:28:59.389009+00	\N
2635	1318	1	2025-05-11	RELATIVE	2025-07-29	79	129.15	1	Delivery option 1 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2636	1318	2	2025-06-01	RELATIVE	2025-07-03	32	159.29	2	Delivery option 2 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2637	1319	1	2025-05-29	RELATIVE	2025-08-25	88	108.21	1	Delivery option 1 for Roofing Membrane - EPDM	t	2025-10-09 13:28:59.389009+00	\N
2638	1319	2	2025-06-16	RELATIVE	2025-08-26	71	118.37	2	Delivery option 2 for Roofing Membrane - EPDM	t	2025-10-09 13:28:59.389009+00	\N
2639	1320	1	2025-03-12	RELATIVE	2025-05-10	59	131.85	1	Delivery option 1 for Perimeter Fencing - Chain Link	t	2025-10-09 13:28:59.389009+00	\N
2640	1320	2	2025-03-19	RELATIVE	2025-05-22	64	95.39	2	Delivery option 2 for Perimeter Fencing - Chain Link	t	2025-10-09 13:28:59.389009+00	\N
2641	1321	1	2025-05-29	RELATIVE	2025-08-15	78	152.71	1	Delivery option 1 for Crane - 50 Ton Capacity	t	2025-10-09 13:28:59.389009+00	\N
2642	1321	2	2025-06-14	RELATIVE	2025-08-25	72	155.77	2	Delivery option 2 for Crane - 50 Ton Capacity	t	2025-10-09 13:28:59.389009+00	\N
2643	1322	1	2025-05-10	RELATIVE	2025-07-05	56	157.29	1	Delivery option 1 for Marble Tiles - 30x30cm	t	2025-10-09 13:28:59.389009+00	\N
2644	1322	2	2025-05-27	RELATIVE	2025-08-01	66	110.67	2	Delivery option 2 for Marble Tiles - 30x30cm	t	2025-10-09 13:28:59.389009+00	\N
2645	1323	1	2025-03-10	RELATIVE	2025-05-10	61	140.50	1	Delivery option 1 for Meeting Room Furniture Set	t	2025-10-09 13:28:59.389009+00	\N
2646	1323	2	2025-03-26	RELATIVE	2025-05-07	42	103.98	2	Delivery option 2 for Meeting Room Furniture Set	t	2025-10-09 13:28:59.389009+00	\N
2647	1324	1	2025-03-31	RELATIVE	2025-05-23	53	134.53	1	Delivery option 1 for Ceramic Tiles - 60x60cm	t	2025-10-09 13:28:59.389009+00	\N
2648	1324	2	2025-04-11	RELATIVE	2025-06-04	54	155.73	2	Delivery option 2 for Ceramic Tiles - 60x60cm	t	2025-10-09 13:28:59.389009+00	\N
2649	1325	1	2025-03-20	RELATIVE	2025-06-04	76	96.93	1	Delivery option 1 for Personal Protective Equipment Set	t	2025-10-09 13:28:59.389009+00	\N
2650	1325	2	2025-03-29	RELATIVE	2025-05-02	34	98.18	2	Delivery option 2 for Personal Protective Equipment Set	t	2025-10-09 13:28:59.389009+00	\N
2651	1326	1	2025-03-28	RELATIVE	2025-05-12	45	145.30	1	Delivery option 1 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2652	1326	2	2025-04-10	RELATIVE	2025-05-30	50	94.38	2	Delivery option 2 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2653	1327	1	2025-03-13	RELATIVE	2025-06-10	89	152.62	1	Delivery option 1 for Ready-Mix Concrete - Grade C25	t	2025-10-09 13:28:59.389009+00	\N
2654	1327	2	2025-04-01	RELATIVE	2025-05-20	49	171.44	2	Delivery option 2 for Ready-Mix Concrete - Grade C25	t	2025-10-09 13:28:59.389009+00	\N
2655	1328	1	2025-03-05	RELATIVE	2025-04-26	52	118.51	1	Delivery option 1 for Water Pipes - PVC 100mm	t	2025-10-09 13:28:59.389009+00	\N
2656	1328	2	2025-03-19	RELATIVE	2025-06-13	86	149.01	2	Delivery option 2 for Water Pipes - PVC 100mm	t	2025-10-09 13:28:59.389009+00	\N
2657	1329	1	2025-03-07	RELATIVE	2025-05-21	75	126.65	1	Delivery option 1 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2658	1329	2	2025-03-18	RELATIVE	2025-05-10	53	109.68	2	Delivery option 2 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2659	1330	1	2025-03-31	RELATIVE	2025-06-14	75	150.07	1	Delivery option 1 for Parking Bollards - Concrete	t	2025-10-09 13:28:59.389009+00	\N
2660	1330	2	2025-04-10	RELATIVE	2025-05-18	38	162.53	2	Delivery option 2 for Parking Bollards - Concrete	t	2025-10-09 13:28:59.389009+00	\N
2661	1331	1	2025-04-26	RELATIVE	2025-06-17	52	103.67	1	Delivery option 1 for LED Light Fixtures - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2662	1331	2	2025-05-17	RELATIVE	2025-06-19	33	163.14	2	Delivery option 2 for LED Light Fixtures - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2663	1332	1	2025-05-02	RELATIVE	2025-06-06	35	157.21	1	Delivery option 1 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2664	1332	2	2025-05-16	RELATIVE	2025-07-08	53	99.00	2	Delivery option 2 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2665	1333	1	2025-05-22	RELATIVE	2025-08-07	77	126.91	1	Delivery option 1 for Ready-Mix Concrete - Grade C25	t	2025-10-09 13:28:59.389009+00	\N
2666	1333	2	2025-06-11	RELATIVE	2025-07-20	39	137.44	2	Delivery option 2 for Ready-Mix Concrete - Grade C25	t	2025-10-09 13:28:59.389009+00	\N
2667	1334	1	2025-05-10	RELATIVE	2025-07-07	58	120.81	1	Delivery option 1 for Interior Paint - Low VOC	t	2025-10-09 13:28:59.389009+00	\N
2668	1334	2	2025-05-20	RELATIVE	2025-08-04	76	97.71	2	Delivery option 2 for Interior Paint - Low VOC	t	2025-10-09 13:28:59.389009+00	\N
2669	1335	1	2025-04-19	RELATIVE	2025-06-17	59	93.54	1	Delivery option 1 for Electrical Conduits - PVC 25mm	t	2025-10-09 13:28:59.389009+00	\N
2670	1335	2	2025-05-01	RELATIVE	2025-07-05	65	144.49	2	Delivery option 2 for Electrical Conduits - PVC 25mm	t	2025-10-09 13:28:59.389009+00	\N
2671	1336	1	2025-04-16	RELATIVE	2025-06-03	48	127.67	1	Delivery option 1 for Power Tools - Construction Set	t	2025-10-09 13:28:59.389009+00	\N
2672	1336	2	2025-05-07	RELATIVE	2025-07-11	65	165.26	2	Delivery option 2 for Power Tools - Construction Set	t	2025-10-09 13:28:59.389009+00	\N
2673	1337	1	2025-03-26	RELATIVE	2025-06-18	84	132.42	1	Delivery option 1 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
2674	1337	2	2025-04-06	RELATIVE	2025-07-04	89	135.25	2	Delivery option 2 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
2675	1338	1	2025-04-28	RELATIVE	2025-06-22	55	95.85	1	Delivery option 1 for Structural Steel Beams - H-Beam 200x200mm	t	2025-10-09 13:28:59.389009+00	\N
2676	1338	2	2025-05-06	RELATIVE	2025-07-04	59	131.18	2	Delivery option 2 for Structural Steel Beams - H-Beam 200x200mm	t	2025-10-09 13:28:59.389009+00	\N
2677	1339	1	2025-05-09	RELATIVE	2025-08-06	89	107.27	1	Delivery option 1 for Aluminum Windows - Double Glazed	t	2025-10-09 13:28:59.389009+00	\N
2678	1339	2	2025-05-18	RELATIVE	2025-07-11	54	113.35	2	Delivery option 2 for Aluminum Windows - Double Glazed	t	2025-10-09 13:28:59.389009+00	\N
2679	1340	1	2025-04-22	RELATIVE	2025-06-08	47	159.73	1	Delivery option 1 for Water Pipes - PVC 100mm	t	2025-10-09 13:28:59.389009+00	\N
2680	1340	2	2025-05-05	RELATIVE	2025-07-31	87	117.53	2	Delivery option 2 for Water Pipes - PVC 100mm	t	2025-10-09 13:28:59.389009+00	\N
2681	1341	1	2025-03-30	RELATIVE	2025-06-16	78	131.70	1	Delivery option 1 for Ventilation Fans - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2682	1341	2	2025-04-11	RELATIVE	2025-06-13	63	139.20	2	Delivery option 2 for Ventilation Fans - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2683	1342	1	2025-04-05	RELATIVE	2025-05-26	51	134.54	1	Delivery option 1 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2684	1342	2	2025-04-15	RELATIVE	2025-07-08	84	118.24	2	Delivery option 2 for Network Equipment - Switch/Router	t	2025-10-09 13:28:59.389009+00	\N
2685	1343	1	2025-03-15	RELATIVE	2025-05-19	65	142.57	1	Delivery option 1 for Directional Signage - Reflective	t	2025-10-09 13:28:59.389009+00	\N
2686	1343	2	2025-04-04	RELATIVE	2025-06-27	84	150.50	2	Delivery option 2 for Directional Signage - Reflective	t	2025-10-09 13:28:59.389009+00	\N
2687	1344	1	2025-05-10	RELATIVE	2025-07-17	68	124.59	1	Delivery option 1 for Landscaping - Trees & Shrubs	t	2025-10-09 13:28:59.389009+00	\N
2688	1344	2	2025-05-18	RELATIVE	2025-06-18	31	138.82	2	Delivery option 2 for Landscaping - Trees & Shrubs	t	2025-10-09 13:28:59.389009+00	\N
2689	1345	1	2025-03-08	RELATIVE	2025-04-07	30	97.70	1	Delivery option 1 for LED Light Fixtures - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2690	1345	2	2025-03-29	RELATIVE	2025-05-12	44	120.15	2	Delivery option 2 for LED Light Fixtures - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2691	1346	1	2025-03-08	RELATIVE	2025-04-17	40	116.41	1	Delivery option 1 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2692	1346	2	2025-03-21	RELATIVE	2025-05-29	69	107.62	2	Delivery option 2 for Cleaning Equipment - Industrial	t	2025-10-09 13:28:59.389009+00	\N
2693	1347	1	2025-05-02	RELATIVE	2025-07-22	81	109.16	1	Delivery option 1 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2694	1347	2	2025-05-17	RELATIVE	2025-06-18	32	122.20	2	Delivery option 2 for Sewage Pipes - HDPE 200mm	t	2025-10-09 13:28:59.389009+00	\N
2695	1348	1	2025-04-27	RELATIVE	2025-07-03	67	114.52	1	Delivery option 1 for Coarse Aggregate - 20mm	t	2025-10-09 13:28:59.389009+00	\N
2696	1348	2	2025-05-17	RELATIVE	2025-08-10	85	107.21	2	Delivery option 2 for Coarse Aggregate - 20mm	t	2025-10-09 13:28:59.389009+00	\N
2697	1349	1	2025-05-12	RELATIVE	2025-06-15	34	163.19	1	Delivery option 1 for Crane - 50 Ton Capacity	t	2025-10-09 13:28:59.389009+00	\N
2698	1349	2	2025-05-28	RELATIVE	2025-07-13	46	139.59	2	Delivery option 2 for Crane - 50 Ton Capacity	t	2025-10-09 13:28:59.389009+00	\N
2699	1350	1	2025-03-06	RELATIVE	2025-05-11	66	163.12	1	Delivery option 1 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
2700	1350	2	2025-03-15	RELATIVE	2025-05-03	49	124.00	2	Delivery option 2 for Reinforcement Bars - Grade 60	t	2025-10-09 13:28:59.389009+00	\N
\.


--
-- Data for Name: finalized_decisions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.finalized_decisions (id, run_id, project_id, project_item_id, item_code, procurement_option_id, purchase_date, delivery_date, quantity, final_cost, status, delivery_option_id, forecast_invoice_timing_type, forecast_invoice_issue_date, forecast_invoice_days_after_delivery, forecast_invoice_amount, actual_invoice_issue_date, actual_invoice_amount, actual_invoice_received_date, invoice_entered_by_id, invoice_entered_at, decision_maker_id, decision_date, finalized_at, finalized_by_id, is_manual_edit, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: optimization_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.optimization_results (id, run_id, run_timestamp, project_id, item_code, procurement_option_id, purchase_time, delivery_time, quantity, final_cost) FROM stdin;
\.


--
-- Data for Name: optimization_runs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.optimization_runs (run_id, run_timestamp, request_parameters, status) FROM stdin;
\.


--
-- Data for Name: procurement_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.procurement_options (id, item_code, supplier_name, base_cost, lomc_lead_time, discount_bundle_threshold, discount_bundle_percent, payment_terms, created_at, updated_at, is_active) FROM stdin;
3901	SECURITY001	Delta Building Solutions	94.32	4	100	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3902	SECURITY001	Alpha Construction Supply	111.13	1	100	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3903	SECURITY001	Zeta Construction	88.94	1	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3904	INSUL002	Delta Building Solutions	106.95	7	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3905	INSUL002	Gamma Industrial	111.91	1	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3906	INSUL002	Theta Supply Chain	111.74	4	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3907	IT002	Mu Construction	105.06	1	100	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3908	IT002	Epsilon Procurement	106.14	4	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3909	IT002	Gamma Industrial	112.34	2	50	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3910	ELEC001	Delta Building Solutions	90.18	6	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3911	ELEC001	Lambda Industrial Supply	104.72	2	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3912	ELEC001	Mu Construction	99.99	1	10	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3913	CLEAN001	Beta Materials Corp	105.13	3	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3914	CLEAN001	Mu Construction	105.51	2	25	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3915	CLEAN001	Alpha Construction Supply	101.28	1	25	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3916	STEEL002	Iota Construction Co	105.23	4	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3917	STEEL002	Alpha Construction Supply	105.98	6	50	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3918	STEEL002	Theta Supply Chain	96.97	5	25	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3919	IT001	Mu Construction	103.24	4	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3920	IT001	Kappa Building Materials	100.42	7	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3921	IT001	Delta Building Solutions	99.60	3	50	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3922	STEEL001	Eta Materials Ltd	112.37	7	25	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3923	STEEL001	Lambda Industrial Supply	112.14	5	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3924	STEEL001	Alpha Construction Supply	104.75	7	100	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3925	SAFETY002	Kappa Building Materials	101.77	5	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3926	SAFETY002	Theta Supply Chain	99.74	5	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3927	SAFETY002	Beta Materials Corp	109.81	2	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3928	LAND001	Theta Supply Chain	92.12	6	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3929	LAND001	Delta Building Solutions	105.87	1	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3930	LAND001	Gamma Industrial	111.46	2	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3931	PARK001	Epsilon Procurement	97.68	3	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3932	PARK001	Beta Materials Corp	112.10	4	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3933	PARK001	Zeta Construction	94.45	3	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3934	PAINT002	Eta Materials Ltd	110.80	6	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3935	PAINT002	Beta Materials Corp	93.27	3	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3936	PAINT002	Theta Supply Chain	105.39	5	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3937	EQUIP003	Gamma Industrial	93.70	4	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3938	EQUIP003	Zeta Construction	113.59	6	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3939	EQUIP003	Iota Construction Co	86.07	1	10	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3940	IT002	Mu Construction	87.70	3	10	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3941	IT002	Gamma Industrial	114.81	4	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3942	IT002	Kappa Building Materials	100.87	4	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3943	FORM002	Gamma Industrial	102.46	7	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3944	FORM002	Epsilon Procurement	103.24	7	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3945	FORM002	Kappa Building Materials	102.77	2	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3946	INSUL001	Beta Materials Corp	112.76	5	10	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3947	INSUL001	Epsilon Procurement	100.02	6	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3948	INSUL001	Lambda Industrial Supply	91.44	5	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3949	HVAC001	Eta Materials Ltd	109.94	2	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3950	HVAC001	Gamma Industrial	114.24	3	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3951	HVAC001	Alpha Construction Supply	95.69	2	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3952	PLUMB002	Delta Building Solutions	108.39	4	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3953	PLUMB002	Mu Construction	110.44	1	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3954	PLUMB002	Alpha Construction Supply	86.32	2	10	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3955	ROOF002	Beta Materials Corp	87.72	4	10	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3956	ROOF002	Epsilon Procurement	86.85	1	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3957	ROOF002	Eta Materials Ltd	92.41	7	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3958	FENCE001	Alpha Construction Supply	95.56	2	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3959	FENCE001	Gamma Industrial	99.76	7	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3960	FENCE001	Kappa Building Materials	102.27	6	50	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3961	EQUIP002	Lambda Industrial Supply	112.92	7	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3962	EQUIP002	Alpha Construction Supply	101.32	1	25	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3963	EQUIP002	Mu Construction	109.65	1	10	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3964	TILE002	Iota Construction Co	96.59	7	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3965	TILE002	Mu Construction	103.59	3	25	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3966	TILE002	Zeta Construction	88.41	6	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3967	FURN002	Lambda Industrial Supply	102.71	7	25	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3968	FURN002	Zeta Construction	85.94	4	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3969	FURN002	Alpha Construction Supply	89.00	6	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3970	TILE001	Theta Supply Chain	96.29	3	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3971	TILE001	Delta Building Solutions	96.33	4	25	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3972	TILE001	Alpha Construction Supply	106.85	3	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3973	SAFETY002	Alpha Construction Supply	105.96	4	50	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
3974	SAFETY002	Eta Materials Ltd	89.27	6	50	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3975	SAFETY002	Kappa Building Materials	108.66	3	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3976	PLUMB002	Mu Construction	90.01	3	10	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3977	PLUMB002	Epsilon Procurement	97.06	6	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3978	PLUMB002	Beta Materials Corp	114.81	5	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3979	CONC001	Mu Construction	92.72	3	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3980	CONC001	Beta Materials Corp	92.17	3	10	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3981	CONC001	Alpha Construction Supply	103.76	5	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3982	PLUMB001	Delta Building Solutions	114.11	2	100	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
3983	PLUMB001	Zeta Construction	98.68	6	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3984	PLUMB001	Gamma Industrial	98.36	5	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3985	IT002	Mu Construction	94.21	6	10	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3986	IT002	Gamma Industrial	87.84	4	10	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3987	IT002	Iota Construction Co	103.24	5	25	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3988	PARK001	Lambda Industrial Supply	102.33	3	25	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3989	PARK001	Mu Construction	95.14	4	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3990	PARK001	Iota Construction Co	91.52	5	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
3991	LIGHT001	Alpha Construction Supply	94.40	2	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3992	LIGHT001	Gamma Industrial	103.02	7	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3993	LIGHT001	Zeta Construction	89.46	7	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3994	CLEAN001	Gamma Industrial	98.85	3	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3995	CLEAN001	Delta Building Solutions	97.69	7	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3996	CLEAN001	Theta Supply Chain	89.45	1	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
3997	CONC001	Lambda Industrial Supply	100.29	7	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
3998	CONC001	Eta Materials Ltd	98.87	5	25	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
3999	CONC001	Gamma Industrial	101.19	4	10	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4000	PAINT002	Alpha Construction Supply	90.17	3	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
4001	PAINT002	Gamma Industrial	90.17	5	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4002	PAINT002	Kappa Building Materials	91.93	4	10	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4003	ELEC002	Beta Materials Corp	98.81	7	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4004	ELEC002	Eta Materials Ltd	91.77	1	10	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4005	ELEC002	Iota Construction Co	97.87	3	25	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4006	TOOL001	Mu Construction	114.51	4	50	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4007	TOOL001	Epsilon Procurement	92.72	6	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4008	TOOL001	Kappa Building Materials	96.07	3	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4009	STEEL002	Beta Materials Corp	87.63	3	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4010	STEEL002	Mu Construction	102.90	7	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4011	STEEL002	Iota Construction Co	91.61	5	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
4012	STEEL001	Beta Materials Corp	108.78	1	100	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4013	STEEL001	Alpha Construction Supply	97.11	4	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4014	STEEL001	Eta Materials Ltd	92.00	2	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4015	WINDOW001	Beta Materials Corp	85.77	4	100	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4016	WINDOW001	Epsilon Procurement	104.16	7	25	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4017	WINDOW001	Alpha Construction Supply	94.76	7	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
4018	PLUMB001	Mu Construction	100.62	2	25	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4019	PLUMB001	Delta Building Solutions	109.38	1	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4020	PLUMB001	Lambda Industrial Supply	100.99	2	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4021	HVAC002	Gamma Industrial	85.90	4	25	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4022	HVAC002	Theta Supply Chain	88.35	4	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4023	HVAC002	Zeta Construction	95.68	5	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4024	IT002	Zeta Construction	92.17	6	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4025	IT002	Alpha Construction Supply	111.11	6	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
4026	IT002	Delta Building Solutions	106.33	1	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4027	SIGN001	Alpha Construction Supply	92.61	4	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4028	SIGN001	Delta Building Solutions	105.30	2	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4029	SIGN001	Beta Materials Corp	106.08	3	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4030	LAND001	Theta Supply Chain	90.19	7	100	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 13:28:59.365893+00	\N	t
4031	LAND001	Delta Building Solutions	111.72	3	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4032	LAND001	Iota Construction Co	111.76	7	10	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4033	LIGHT001	Epsilon Procurement	99.53	5	25	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4034	LIGHT001	Iota Construction Co	92.30	6	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4035	LIGHT001	Zeta Construction	87.84	3	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4036	CLEAN001	Alpha Construction Supply	106.74	5	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4037	CLEAN001	Delta Building Solutions	86.41	7	25	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4038	CLEAN001	Beta Materials Corp	94.92	1	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 13:28:59.365893+00	\N	t
4039	PLUMB002	Gamma Industrial	92.39	7	50	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 13:28:59.365893+00	\N	t
4040	PLUMB002	Kappa Building Materials	102.08	2	100	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4041	PLUMB002	Iota Construction Co	95.98	3	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4042	AGG001	Lambda Industrial Supply	103.92	7	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4043	AGG001	Epsilon Procurement	98.73	6	10	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4044	AGG001	Iota Construction Co	110.01	2	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4045	EQUIP002	Delta Building Solutions	97.24	5	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4046	EQUIP002	Eta Materials Ltd	86.24	1	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4047	EQUIP002	Kappa Building Materials	105.91	6	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 13:28:59.365893+00	\N	t
4048	STEEL002	Kappa Building Materials	88.30	3	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
4049	STEEL002	Beta Materials Corp	94.41	7	100	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 13:28:59.365893+00	\N	t
4050	STEEL002	Alpha Construction Supply	91.26	4	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 13:28:59.365893+00	\N	t
\.


--
-- Data for Name: project_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_assignments (user_id, project_id, assigned_at) FROM stdin;
184	131	2025-10-09 13:28:59.306772+00
185	132	2025-10-09 13:28:59.306772+00
184	133	2025-10-09 13:28:59.306772+00
185	134	2025-10-09 13:28:59.306772+00
184	135	2025-10-09 13:28:59.306772+00
\.


--
-- Data for Name: project_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_items (id, project_id, item_code, item_name, quantity, delivery_options, status, external_purchase, decision_date, procurement_date, payment_date, invoice_submission_date, expected_cash_in_date, actual_cash_in_date, created_at, updated_at) FROM stdin;
1301	131	SECURITY001	Security Cameras - IP Network	7	["2025-04-23", "2025-05-01", "2025-06-02"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1302	131	INSUL002	Acoustic Insulation - Fiberglass	11	["2025-03-28", "2025-04-12", "2025-05-01", "2025-05-09"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1303	131	IT002	Network Equipment - Switch/Router	3	["2025-03-11", "2025-03-31", "2025-04-04", "2025-04-04"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1304	131	ELEC001	Electrical Cables - 3-Core 2.5mm²	3	["2025-03-23", "2025-04-04"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1305	131	CLEAN001	Cleaning Equipment - Industrial	16	["2025-04-04", "2025-04-18", "2025-05-06"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1306	131	STEEL002	Reinforcement Bars - Grade 60	12	["2025-05-05", "2025-05-13"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1307	131	IT001	Computer Equipment - Desktop	13	["2025-05-29", "2025-06-17", "2025-06-20", "2025-07-10"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1308	131	STEEL001	Structural Steel Beams - H-Beam 200x200mm	4	["2025-04-15", "2025-04-29", "2025-05-17", "2025-05-06"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1309	131	SAFETY002	Personal Protective Equipment Set	12	["2025-05-24", "2025-06-07", "2025-07-05"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1310	131	LAND001	Landscaping - Trees & Shrubs	10	["2025-03-12", "2025-03-24"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1311	132	PARK001	Parking Bollards - Concrete	12	["2025-03-09", "2025-03-18"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1312	132	PAINT002	Interior Paint - Low VOC	12	["2025-03-20", "2025-04-01", "2025-04-21", "2025-05-16"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1313	132	EQUIP003	Concrete Mixer - 3m³	4	["2025-03-12", "2025-03-23"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1314	132	IT002	Network Equipment - Switch/Router	5	["2025-05-16", "2025-05-30", "2025-06-11"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1315	132	FORM002	Formwork - Plywood Sheets	3	["2025-03-23", "2025-04-03", "2025-04-16"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1316	132	INSUL001	Thermal Insulation - Rockwool	9	["2025-03-07", "2025-03-27"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1317	132	HVAC001	Air Conditioning Units - Split Type	14	["2025-05-29", "2025-06-12"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1318	132	PLUMB002	Sewage Pipes - HDPE 200mm	14	["2025-05-11", "2025-06-01", "2025-05-27", "2025-07-01"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1319	132	ROOF002	Roofing Membrane - EPDM	9	["2025-05-29", "2025-06-16", "2025-07-06", "2025-07-31"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1320	132	FENCE001	Perimeter Fencing - Chain Link	9	["2025-03-12", "2025-03-19", "2025-04-07"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1321	133	EQUIP002	Crane - 50 Ton Capacity	13	["2025-05-29", "2025-06-14", "2025-06-26"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1322	133	TILE002	Marble Tiles - 30x30cm	15	["2025-05-10", "2025-05-27", "2025-06-21", "2025-07-06"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1323	133	FURN002	Meeting Room Furniture Set	18	["2025-03-10", "2025-03-26"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1324	133	TILE001	Ceramic Tiles - 60x60cm	6	["2025-03-31", "2025-04-11", "2025-05-04"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1325	133	SAFETY002	Personal Protective Equipment Set	1	["2025-03-20", "2025-03-29"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1326	133	PLUMB002	Sewage Pipes - HDPE 200mm	8	["2025-03-28", "2025-04-10", "2025-04-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1327	133	CONC001	Ready-Mix Concrete - Grade C25	7	["2025-03-13", "2025-04-01"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1328	133	PLUMB001	Water Pipes - PVC 100mm	2	["2025-03-05", "2025-03-19", "2025-03-27"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1329	133	IT002	Network Equipment - Switch/Router	1	["2025-03-07", "2025-03-18", "2025-03-27", "2025-04-06"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1330	133	PARK001	Parking Bollards - Concrete	2	["2025-03-31", "2025-04-10", "2025-05-10", "2025-05-24"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1331	134	LIGHT001	LED Light Fixtures - Industrial	10	["2025-04-26", "2025-05-17"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1332	134	CLEAN001	Cleaning Equipment - Industrial	18	["2025-05-02", "2025-05-16", "2025-05-28", "2025-05-23"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1333	134	CONC001	Ready-Mix Concrete - Grade C25	14	["2025-05-22", "2025-06-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1334	134	PAINT002	Interior Paint - Low VOC	6	["2025-05-10", "2025-05-20"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1335	134	ELEC002	Electrical Conduits - PVC 25mm	1	["2025-04-19", "2025-05-01"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1336	134	TOOL001	Power Tools - Construction Set	10	["2025-04-16", "2025-05-07", "2025-05-24", "2025-05-07"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1337	134	STEEL002	Reinforcement Bars - Grade 60	12	["2025-03-26", "2025-04-06", "2025-04-09"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1338	134	STEEL001	Structural Steel Beams - H-Beam 200x200mm	19	["2025-04-28", "2025-05-06", "2025-05-28", "2025-05-19"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1339	134	WINDOW001	Aluminum Windows - Double Glazed	9	["2025-05-09", "2025-05-18", "2025-06-04"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1340	134	PLUMB001	Water Pipes - PVC 100mm	19	["2025-04-22", "2025-05-05"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1341	135	HVAC002	Ventilation Fans - Industrial	2	["2025-03-30", "2025-04-11", "2025-05-01"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1342	135	IT002	Network Equipment - Switch/Router	14	["2025-04-05", "2025-04-15", "2025-05-15"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1343	135	SIGN001	Directional Signage - Reflective	16	["2025-03-15", "2025-04-04", "2025-04-16", "2025-04-08"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1344	135	LAND001	Landscaping - Trees & Shrubs	13	["2025-05-10", "2025-05-18"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1345	135	LIGHT001	LED Light Fixtures - Industrial	20	["2025-03-08", "2025-03-29", "2025-04-09", "2025-04-13"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1346	135	CLEAN001	Cleaning Equipment - Industrial	16	["2025-03-08", "2025-03-21"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1347	135	PLUMB002	Sewage Pipes - HDPE 200mm	1	["2025-05-02", "2025-05-17", "2025-05-22", "2025-06-04"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1348	135	AGG001	Coarse Aggregate - 20mm	9	["2025-04-27", "2025-05-17", "2025-05-11"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1349	135	EQUIP002	Crane - 50 Ton Capacity	7	["2025-05-12", "2025-05-28", "2025-05-26"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
1350	135	STEEL002	Reinforcement Bars - Grade 60	16	["2025-03-06", "2025-03-15"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 13:28:59.331588+00	\N
\.


--
-- Data for Name: project_phases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_phases (id, project_id, phase_name, start_date, end_date, created_at, updated_at) FROM stdin;
521	131	Phase 1: Planning & Design	2025-01-01	2025-02-15	2025-10-09 13:28:59.320433+00	\N
522	131	Phase 2: Site Preparation	2025-02-16	2025-04-01	2025-10-09 13:28:59.320433+00	\N
523	131	Phase 3: Construction	2025-04-02	2025-06-30	2025-10-09 13:28:59.320433+00	\N
524	131	Phase 4: Finishing & Testing	2025-07-01	2025-08-29	2025-10-09 13:28:59.320433+00	\N
525	132	Phase 1: Planning & Design	2025-03-02	2025-04-16	2025-10-09 13:28:59.320433+00	\N
526	132	Phase 2: Site Preparation	2025-04-17	2025-05-31	2025-10-09 13:28:59.320433+00	\N
527	132	Phase 3: Construction	2025-06-01	2025-08-29	2025-10-09 13:28:59.320433+00	\N
528	132	Phase 4: Finishing & Testing	2025-08-30	2025-10-28	2025-10-09 13:28:59.320433+00	\N
529	133	Phase 1: Planning & Design	2025-05-01	2025-06-15	2025-10-09 13:28:59.320433+00	\N
530	133	Phase 2: Site Preparation	2025-06-16	2025-07-30	2025-10-09 13:28:59.320433+00	\N
531	133	Phase 3: Construction	2025-07-31	2025-10-28	2025-10-09 13:28:59.320433+00	\N
532	133	Phase 4: Finishing & Testing	2025-10-29	2025-12-27	2025-10-09 13:28:59.320433+00	\N
533	134	Phase 1: Planning & Design	2025-06-30	2025-08-14	2025-10-09 13:28:59.320433+00	\N
534	134	Phase 2: Site Preparation	2025-08-15	2025-09-28	2025-10-09 13:28:59.320433+00	\N
535	134	Phase 3: Construction	2025-09-29	2025-12-27	2025-10-09 13:28:59.320433+00	\N
536	134	Phase 4: Finishing & Testing	2025-12-28	2026-02-25	2025-10-09 13:28:59.320433+00	\N
537	135	Phase 1: Planning & Design	2025-08-29	2025-10-13	2025-10-09 13:28:59.320433+00	\N
538	135	Phase 2: Site Preparation	2025-10-14	2025-11-27	2025-10-09 13:28:59.320433+00	\N
539	135	Phase 3: Construction	2025-11-28	2026-02-25	2025-10-09 13:28:59.320433+00	\N
540	135	Phase 4: Finishing & Testing	2026-02-26	2026-04-26	2025-10-09 13:28:59.320433+00	\N
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.projects (id, project_code, name, priority_weight, created_at, is_active) FROM stdin;
131	INFRA001	Highway Infrastructure Project	9	2025-10-09 13:28:59.300148+00	t
132	BUILD002	Commercial Building Complex	8	2025-10-09 13:28:59.300148+00	t
133	RESI003	Residential Housing Development	7	2025-10-09 13:28:59.300148+00	t
134	INDU004	Industrial Manufacturing Plant	6	2025-10-09 13:28:59.300148+00	t
135	UTIL005	Utilities Infrastructure Upgrade	5	2025-10-09 13:28:59.300148+00	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password_hash, role, created_at, is_active) FROM stdin;
183	admin	$2b$12$RXVUCXPhcoFMBe3z2ZS36.PmJHdGXtAi0mL9nAz4IQD82jkT/kAZ6	admin	2025-10-09 13:28:59.288233+00	t
184	pm1	$2b$12$w7LKUV9ZiYx/euMt588hW.XkvR1NWbfpgKcYtly0hk6hDZflqEmmy	pm	2025-10-09 13:28:59.288233+00	t
185	pm2	$2b$12$wzqFWr5M70O7W2Ir3UuLie4XPjAPrU.NC3zYPawQFhk00trYc7R9q	pm	2025-10-09 13:28:59.288233+00	t
186	proc1	$2b$12$nClDrsfbj6SYmvb5mBhmFOnxd6IBVTNjTEzf9Fta8KUrP/vCOhrcy	procurement	2025-10-09 13:28:59.288233+00	t
187	proc2	$2b$12$odcokhgtJCRpzVGV1mqdfe91c.FFBWOx0s/GaQc5.82M3fiT7Z6fG	procurement	2025-10-09 13:28:59.288233+00	t
188	finance1	$2b$12$Kf9CdpBkKopde9AjZMJ.hOWQPnq1g.Jsu06frCG1d9uO/FSWzLFg2	finance	2025-10-09 13:28:59.288233+00	t
189	finance2	$2b$12$yYoN0SCZ4UigqxoRPuH6yOdzf0iBi4LhaEWLl1CCy5gvQEDG1s3jW	finance	2025-10-09 13:28:59.288233+00	t
\.


--
-- Name: budget_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.budget_data_id_seq', 324, true);


--
-- Name: cashflow_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cashflow_events_id_seq', 248, true);


--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.decision_factor_weights_id_seq', 216, true);


--
-- Name: delivery_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.delivery_options_id_seq', 2700, true);


--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.finalized_decisions_id_seq', 105, true);


--
-- Name: optimization_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.optimization_results_id_seq', 145, true);


--
-- Name: procurement_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.procurement_options_id_seq', 4050, true);


--
-- Name: project_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.project_items_id_seq', 1350, true);


--
-- Name: project_phases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.project_phases_id_seq', 540, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.projects_id_seq', 135, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 189, true);


--
-- Name: budget_data budget_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_data
    ADD CONSTRAINT budget_data_pkey PRIMARY KEY (id);


--
-- Name: cashflow_events cashflow_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_pkey PRIMARY KEY (id);


--
-- Name: decision_factor_weights decision_factor_weights_factor_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights
    ADD CONSTRAINT decision_factor_weights_factor_name_key UNIQUE (factor_name);


--
-- Name: decision_factor_weights decision_factor_weights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights
    ADD CONSTRAINT decision_factor_weights_pkey PRIMARY KEY (id);


--
-- Name: delivery_options delivery_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options
    ADD CONSTRAINT delivery_options_pkey PRIMARY KEY (id);


--
-- Name: finalized_decisions finalized_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_pkey PRIMARY KEY (id);


--
-- Name: optimization_results optimization_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_pkey PRIMARY KEY (id);


--
-- Name: optimization_runs optimization_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_runs
    ADD CONSTRAINT optimization_runs_pkey PRIMARY KEY (run_id);


--
-- Name: procurement_options procurement_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_options
    ADD CONSTRAINT procurement_options_pkey PRIMARY KEY (id);


--
-- Name: project_assignments project_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_pkey PRIMARY KEY (user_id, project_id);


--
-- Name: project_items project_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items
    ADD CONSTRAINT project_items_pkey PRIMARY KEY (id);


--
-- Name: project_phases project_phases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases
    ADD CONSTRAINT project_phases_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_budget_data_budget_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_budget_data_budget_date ON public.budget_data USING btree (budget_date);


--
-- Name: ix_budget_data_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_budget_data_id ON public.budget_data USING btree (id);


--
-- Name: ix_cashflow_events_event_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_event_date ON public.cashflow_events USING btree (event_date);


--
-- Name: ix_cashflow_events_forecast_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_forecast_type ON public.cashflow_events USING btree (forecast_type);


--
-- Name: ix_cashflow_events_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_id ON public.cashflow_events USING btree (id);


--
-- Name: ix_cashflow_events_is_cancelled; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_is_cancelled ON public.cashflow_events USING btree (is_cancelled);


--
-- Name: ix_decision_factor_weights_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_decision_factor_weights_id ON public.decision_factor_weights USING btree (id);


--
-- Name: ix_delivery_options_delivery_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_delivery_date ON public.delivery_options USING btree (delivery_date);


--
-- Name: ix_delivery_options_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_id ON public.delivery_options USING btree (id);


--
-- Name: ix_delivery_options_project_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_project_item_id ON public.delivery_options USING btree (project_item_id);


--
-- Name: ix_finalized_decisions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_id ON public.finalized_decisions USING btree (id);


--
-- Name: ix_finalized_decisions_item_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_item_code ON public.finalized_decisions USING btree (item_code);


--
-- Name: ix_finalized_decisions_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_run_id ON public.finalized_decisions USING btree (run_id);


--
-- Name: ix_finalized_decisions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_status ON public.finalized_decisions USING btree (status);


--
-- Name: ix_optimization_results_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_optimization_results_id ON public.optimization_results USING btree (id);


--
-- Name: ix_optimization_results_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_optimization_results_run_id ON public.optimization_results USING btree (run_id);


--
-- Name: ix_procurement_options_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_procurement_options_id ON public.procurement_options USING btree (id);


--
-- Name: ix_procurement_options_item_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_procurement_options_item_code ON public.procurement_options USING btree (item_code);


--
-- Name: ix_project_items_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_project_items_id ON public.project_items USING btree (id);


--
-- Name: ix_project_phases_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_project_phases_id ON public.project_phases USING btree (id);


--
-- Name: ix_projects_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_projects_id ON public.projects USING btree (id);


--
-- Name: ix_projects_project_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_projects_project_code ON public.projects USING btree (project_code);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: cashflow_events cashflow_events_cancelled_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_cancelled_by_id_fkey FOREIGN KEY (cancelled_by_id) REFERENCES public.users(id);


--
-- Name: cashflow_events cashflow_events_related_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_related_decision_id_fkey FOREIGN KEY (related_decision_id) REFERENCES public.finalized_decisions(id) ON DELETE CASCADE;


--
-- Name: delivery_options delivery_options_project_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options
    ADD CONSTRAINT delivery_options_project_item_id_fkey FOREIGN KEY (project_item_id) REFERENCES public.project_items(id) ON DELETE CASCADE;


--
-- Name: finalized_decisions finalized_decisions_decision_maker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_decision_maker_id_fkey FOREIGN KEY (decision_maker_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_delivery_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_delivery_option_id_fkey FOREIGN KEY (delivery_option_id) REFERENCES public.delivery_options(id);


--
-- Name: finalized_decisions finalized_decisions_finalized_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_finalized_by_id_fkey FOREIGN KEY (finalized_by_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_invoice_entered_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_invoice_entered_by_id_fkey FOREIGN KEY (invoice_entered_by_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_procurement_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_procurement_option_id_fkey FOREIGN KEY (procurement_option_id) REFERENCES public.procurement_options(id);


--
-- Name: finalized_decisions finalized_decisions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: finalized_decisions finalized_decisions_project_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_project_item_id_fkey FOREIGN KEY (project_item_id) REFERENCES public.project_items(id) ON DELETE CASCADE;


--
-- Name: finalized_decisions finalized_decisions_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.optimization_runs(run_id);


--
-- Name: optimization_results optimization_results_procurement_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_procurement_option_id_fkey FOREIGN KEY (procurement_option_id) REFERENCES public.procurement_options(id);


--
-- Name: optimization_results optimization_results_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_assignments project_assignments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_assignments project_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_items project_items_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items
    ADD CONSTRAINT project_items_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_phases project_phases_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases
    ADD CONSTRAINT project_phases_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 01Jj6bA0CjbIPRjgeeCLcWjFn6bsc53dugbYT6uFj3bcH7ya7Qc4XjdKbbmtHCu

