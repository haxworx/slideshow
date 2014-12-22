#! /usr/bin/perl

use strict;
use warnings;

use CGI qw/:standard/;

require './config.pl';

my $cgi = CGI->new();

my $code = $cgi->param("key");
my $dbh = dbh_connect();

my $SQL = "UPDATE users SET active = 1 WHERE code = ?";
my $sth = $dbh->prepare($SQL);
$sth->execute($code);

$SQL = "SELECT username FROM users WHERE active = 1 AND code = ?";

$sth = $dbh->prepare($SQL);
$sth->execute($code);
my $result = $sth->fetchrow();
if ($result ne "") {
	browser_message("Your account is now activated and ready to use.");
} else {
	browser_message("Invalid activation code.");
}

exit 0;
