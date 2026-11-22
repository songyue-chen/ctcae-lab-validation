/*------------------------------------------------------------------------------------------------
  selfcheck.sas - proves that the loader and the comparator work in this SAS session, without any
  grading implementation: the published expectations themselves play the part of a perfect
  implementation, then they are corrupted on purpose.

  1. Set ctcval_dir below to the folder that holds data/ and reference/.
  2. Run in SAS Enterprise Guide or in batch.
  3. The log must end with "SELFCHECK PASSED" and contain no ERROR line.
------------------------------------------------------------------------------------------------*/
%let ctcval_dir=/path/to/ctcae-lab-validation;

%include "&ctcval_dir/reference/sas/load_records.sas";
%include "&ctcval_dir/reference/sas/compare_results.sas";
%ctcval_load(dir=&ctcval_dir);

%global selfcheck_fail;
%let selfcheck_fail=0;
%macro expect(status=, mismatches=, label=);
  %if &ctcval_status ne &status or &ctcval_mismatches ne &mismatches %then %do;
    %let selfcheck_fail=1;
    %put ERROR: selfcheck &label - expected &status with &mismatches mismatches but got &ctcval_status with &ctcval_mismatches;
  %end;
  %else %put NOTE: selfcheck &label - ok (&status with &mismatches mismatches);
%mend expect;

/* 1. a perfect bidirectional implementation of CTCAE v5 (the wide expectation columns) */
data perfect_v5;
  set ctcval_records;
  GRL=EXP_GRADE_LOW_V5;
  GRH=EXP_GRADE_HIGH_V5;
  TRL=EXP_TERM_LOW_V5;
  TRH=EXP_TERM_HIGH_V5;
  keep RECORD_ID GRL GRH TRL TRH;
run;
%ctcval_compare(results=perfect_v5, version=5, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, print=N);
%expect(status=PASS, mismatches=0, label=1 perfect bidirectional v5);

/* 2. a perfect single-scale implementation of CTCAE v6 */
data perfect_v6;
  set ctcval_records;
  keep RECORD_ID EXP_GRADE_V6 EXP_TERM_V6;
run;
%ctcval_compare(results=perfect_v6, version=6, grade=EXP_GRADE_V6, term=EXP_TERM_V6, print=N);
%expect(status=PASS, mismatches=0, label=2 perfect single-scale v6);

/* 3. four corrupted records: three grades raised, one record removed, one term written in lower case with blanks
      (case and blanks never count) */
data corrupt_v5;
  set perfect_v5;
  if _n_ in (2, 3, 4) then GRL=sum(GRL, 1);
  if _n_=5 then delete;
  if _n_=6 then TRL=lowcase(TRL)||'   ';
run;
%ctcval_compare(results=corrupt_v5, version=5, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, print=N);
%expect(status=FAIL, mismatches=4, label=3 corrupted bidirectional v5);

/* 4. the module filter: the corrupted records are CORE records, so UNITS and CATEGORY still pass */
%ctcval_compare(results=corrupt_v5, version=5, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, modules=UNITS CATEGORY, print=N);
%expect(status=PASS, mismatches=0, label=4 module filter);

/* 5. grades only (terms not compared) and the convention-dependent records excluded */
%ctcval_compare(results=perfect_v5, version=5, gradelow=GRL, gradehigh=GRH, convdep=N, print=N);
%expect(status=PASS, mismatches=0, label=5 grades only without convention-dependent records);

/* 6. an alternative profile: perfect results built from the BESTCASE_ENZYMES rows pass under that profile,
      and the DEFAULT results fail under it on exactly the records the profile changes */
proc sql noprint;
  select count(distinct a.RECORD_ID) into :n_bestcase trimmed
  from ctcval_expectations as a, ctcval_expectations as d
  where a.VERSION=5 and a.PROFILE='BESTCASE_ENZYMES' and d.VERSION=5 and d.PROFILE='DEFAULT'
    and a.RECORD_ID=d.RECORD_ID and a.DIRECTION=d.DIRECTION and a.DIRECTION in ('LOW', 'HIGH')
    and (coalesce(a.GRADE, -1) ne coalesce(d.GRADE, -1) or a.TERM ne d.TERM);
quit;
data alt_low alt_high;
  set ctcval_expectations;
  where VERSION=5 and PROFILE='BESTCASE_ENZYMES';
  if DIRECTION='LOW' then output alt_low;
  else if DIRECTION='HIGH' then output alt_high;
  keep RECORD_ID GRADE TERM;
run;
proc sort data=alt_low; by RECORD_ID; run;
proc sort data=alt_high; by RECORD_ID; run;
data bestcase_v5;
  merge perfect_v5 alt_low(in=_l rename=(GRADE=_gl TERM=_tl)) alt_high(in=_h rename=(GRADE=_gh TERM=_th));
  by RECORD_ID;
  if _l then do; GRL=_gl; TRL=_tl; end;
  if _h then do; GRH=_gh; TRH=_th; end;
  drop _gl _tl _gh _th;
run;
%ctcval_compare(results=bestcase_v5, version=5, profile=BESTCASE_ENZYMES, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, print=N);
%expect(status=PASS, mismatches=0, label=6a perfect BESTCASE_ENZYMES v5);
%ctcval_compare(results=perfect_v5, version=5, profile=BESTCASE_ENZYMES, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, print=N);
%expect(status=FAIL, mismatches=&n_bestcase, label=6b DEFAULT results under BESTCASE_ENZYMES v5);

/* 7. the ADaM and SDTM namings load */
%ctcval_load(dir=&ctcval_dir, naming=ADAM, prefix=adam_);
%ctcval_load(dir=&ctcval_dir, naming=SDTM, prefix=sdtm_);
proc sql noprint;
  select count(*) into :n_adam trimmed from adam_records where not missing(AVAL) and not missing(ADT);
  select count(*) into :n_sdtm trimmed from sdtm_records where not missing(LBSTRESN) and LBDTC ne '';
quit;
%macro namings;
  %if &n_adam ne &n_sdtm or &n_adam=0 %then %do;
    %let selfcheck_fail=1;
    %put ERROR: selfcheck 7 namings - ADaM and SDTM loads differ (&n_adam vs &n_sdtm records with a value);
  %end;
  %else %put NOTE: selfcheck 7 namings - ok (&n_adam records with a value under both namings);
%mend namings;
%namings;
/* 7b. the comparator works on the SDTM-named load (STATUS is renamed LBSTAT there) */
data perfect_sdtm;
  set sdtm_records;
  GRL=EXP_GRADE_LOW_V5;
  GRH=EXP_GRADE_HIGH_V5;
  keep RECORD_ID GRL GRH;
run;
%ctcval_compare(results=perfect_sdtm, version=5, gradelow=GRL, gradehigh=GRH, prefix=sdtm_, print=N);
%expect(status=PASS, mismatches=0, label=7b comparison on the SDTM-named load);

/* one printed example of the report */
%ctcval_compare(results=corrupt_v5, version=5, gradelow=GRL, gradehigh=GRH, termlow=TRL, termhigh=TRH, modules=CORE);

%macro verdict;
  %if &selfcheck_fail=0 %then %put NOTE: SELFCHECK PASSED - loader and comparator work in this session;
  %else %put ERROR: SELFCHECK FAILED - see the ERROR lines above;
%mend verdict;
%verdict;
