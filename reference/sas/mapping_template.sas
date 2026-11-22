/*------------------------------------------------------------------------------------------------
  mapping_template.sas - where an adopter connects the dataset to a grading macro (template, edit freely)

  The dataset is implementation-free: records carry CDISC LBTESTCD / LBSPEC codes, neutral or ADaM / SDTM
  variable names (see %ctcval_load naming=), the result as received (VAL, UNIT, LLN, ULN) and the baseline
  both as a flagged record and as BASE_* columns. Four things usually need mapping:
    1. your test codes      -> recode LBTESTCD (or PARAMCD) into the codes your macro expects
    2. your categories      -> derive a category from LBSPEC when your macro joins on one
    3. your variable names  -> rename what %ctcval_load does not already provide
    4. your term names      -> after grading, map internal term text to the official CTCAE term text
  Then call %ctcval_compare on the macro output.
------------------------------------------------------------------------------------------------*/
%let ctcval_dir=/path/to/ctcae-lab-validation;
%include "&ctcval_dir/reference/sas/load_records.sas";
%include "&ctcval_dir/reference/sas/compare_results.sas";
%ctcval_load(dir=&ctcval_dir, naming=ADAM);

data lab_for_grading;
  set ctcval_records;
  /* 1. test codes: one WHEN per code that differs from the CDISC LBTESTCD (examples only) */
  length MYPARAMCD $8;
  select (PARAMCD);
    when ('CK')       MYPARAMCD='MYCK';
    when ('LIPASET')  MYPARAMCD='MYLIP';
    when ('GFRBSCRT') MYPARAMCD='MYEGFR';
    otherwise         MYPARAMCD=PARAMCD;
  end;
  /* 2. category from the specimen, when your macro joins on one */
  length PARCAT1 $40;
  select (LBSPEC);
    when ('URINE') PARCAT1='URINALYSIS';
    when ('BLOOD') PARCAT1='HEMATOLOGY';
    otherwise      PARCAT1='CHEMISTRY';
  end;
  /* 3. further renames or derivations your macro expects go here */
run;

/*  run your grading macro on lab_for_grading here, once per CTCAE version, e.g.
    %mygrade(data=lab_for_grading, out=graded_v5, version=5, paramcd=MYPARAMCD, aval=AVAL, unit=AVALU, lo=ANRLO, hi=ANRHI);
*/

data my_results_v5;
  set graded_v5;
  /* 4. map internal term names to the official CTCAE term text when they differ (examples only) */
  length TERMLOW TERMHIGH $60;
  TERMLOW=ATOXDSCL;
  TERMHIGH=ATOXDSCH;
  if upcase(ATOXDSCH)='CPK INCREASED' then TERMHIGH='CPK increased';
  keep RECORD_ID ATOXGRL ATOXGRH TERMLOW TERMHIGH;
run;

%ctcval_compare(results=my_results_v5, version=5, profile=DEFAULT,
                gradelow=ATOXGRL, gradehigh=ATOXGRH, termlow=TERMLOW, termhigh=TERMHIGH);
/* single-scale designs: %ctcval_compare(results=my_results_v5, version=5, grade=ATOXGR, term=ATOXDSC); */
