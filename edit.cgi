#!/usr/bin/perl

use strict;
use warnings;

use CGI qw/:standard/;
use Template;
use Mail;
use DBI;
use CGI::Cookie;

require './config.pl';

our $DISK_USAGE;

my $cgi = CGI->new();
my $action = $cgi->param("action");
if ($action eq "logout") {
	my $cookie = cookie( -name => "auth",
		             -value => 0);
	print "Set-Cookie: $cookie\n";
        print $cgi->redirect("/");
        exit 0;
}

my $username = $cgi->cookie("username");
my $password = $cgi->param("password");
my $cookie = $cgi->cookie("auth");

my $status = check_cookie($cookie, $username);
my $directory = $cgi->param("directory");

if ($status) {
        $username = $cgi->cookie("username");
        my $dbh = dbh_connect();
        my $SQL = "SELECT password FROM users WHERE username = ?";
        my $sth = $dbh->prepare($SQL);
        $sth->execute($username);
        $password = $sth->fetchrow();
} else {
        $username = $cgi->param("username");
        $password = $cgi->param("password");
        if ($password eq "") {
                $password = $cgi->cookie("password");
        }
if ($username eq "") {
        browser_message("You did not input a valid username." , "");
}
if ($password eq "") {
        $password = $cgi->param("password");
}
if ($password eq "") {
        browser_message("You did not input a valid password.", "");
}
}

if ($password eq "") {
	$password = $cgi->param("password");
}

my $filename = $cgi->param("filename");

my $path = "users/$directory/$filename";

if ($action eq "save") {
	my $portfolio = "users/$username/index.html";
	$path = $portfolio;
	open(FH, ">$path") || die "Sqwark!\n";
	
	my $html = $cgi->param("text");
	print FH $html;
	close FH;
	
	browser_message("Portfolio saved!");
}

if ($action eq "edit") {
	print "Content-type: text/html\r\n\r\n";
	open(FH, "$path") || die "Error!\n";
	my @content = <FH>; # Load file from disk into memory.
	
	close FH;
	my $html = "@content";

	my $vars = {
		HTML => $html,
		FILENAME => $filename,
		DIRECTORY => $directory,
	};
	
	my $template = Template->new();
	my $editor_template = "templates/editor";
	$template->process($editor_template, $vars) or print "bakaak! kwar kwa $!\n\n";
}
	
exit 0;


