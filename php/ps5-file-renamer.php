<?php
// DEPRECATED - Converted to the Python version
//
// PS5 File Renamer
// Scans the PS5 Video Clips and Screenshots directories and renames files based on the
// folder they are in, adding a sequential number to the end.
// Creates _scanned.json and _originals.json files to keep track of processed files

const VID_DIR = "./PS5/CREATE/Video Clips";  //Video Directory to be scanned
const PIC_DIR = "./PS5/CREATE/Screenshots";  //Screenshot Directory to be scanned

$scanDirs = [VID_DIR,PIC_DIR];

$array_ignored_files = array(
    ".",
    "..",
    ".DS_Store",
    "_scanned.json",
    "_originals.json",
    basename(__FILE__)
);

function consoleLog($msg, $sleepTime=0, $isArray=false){
    echo ($isArray) ? print_r($msg) : $msg;
    echo PHP_EOL;
    sleep($sleepTime);
}

function loadJson($dir){
    $filePath = $dir."/_scanned.json";
    $prevScanned = [];

    if(is_file($filePath)){
        $jsonOutput  = file_get_contents($filePath);
        $scanned = json_decode($jsonOutput,true);
        $prevScanned = array_merge($prevScanned, $scanned);
    }
    return $prevScanned;
}

function loadOGJson($dir){
    $filePath = $dir."/_originals.json";
    $prevScanned = [];

    if(is_file($filePath)){
        $jsonOutput  = file_get_contents($filePath);
        $scanned = json_decode($jsonOutput,true);
        $prevScanned = array_merge($prevScanned, $scanned);
    }
    return $prevScanned;
}

foreach ($scanDirs as $scanD)
{
    if (is_dir($scanD))
    {
        $arrDir = array_diff(scandir($scanD), $array_ignored_files);  //Scan the $DocDirectory and create an array list of all of the files and directories
        natcasesort($arrDir);
        if( isset($arrDir) && is_array($arrDir) )
        {
            foreach( $arrDir as $dir )   //For each document in the current document array
            {
                $prevScanned = loadJson($scanD ."/".$dir);
                $prevOGScanned = loadOGJson($scanD ."/".$dir);
                consoleLog("Scanning " . $scanD ."/". $dir,1);
                if(is_dir($scanD ."/".$dir))
                {
                    $arrFiles = array_diff(scandir($scanD ."/".$dir), $array_ignored_files);  //Scan the $DocDirectory and create an array list of all of the files and directories
                    natcasesort($arrFiles);
                    if(isset($arrFiles) && is_array($arrFiles))
                    {
                        $ctr=0;
                        $processedFiles = [];
                        $processedOGFiles = [];
                        foreach( $arrFiles as $a )   //For each document in the current document array
                        {
                            if(!in_array($a,$prevScanned))
                            {
                                $oldFileName = pathinfo( $a, PATHINFO_FILENAME ) . "." . pathinfo($a, PATHINFO_EXTENSION);

                                // Directory with Files search and count
                                if( is_file($scanD . "/" . $dir . "/" . $a) && !in_array($a,$array_ignored_files) && substr($a,strlen($a)-3,3) != ".db")      //The "." and ".." are directories.  "." is the current and ".." is the parent
                                {
                                    $dirCleaned = preg_replace("/[^A-Za-z0-9 ]/", '', $dir);   // Only use Alphanumeric titles
                                    $newname = str_replace(" ", "-", $dirCleaned) . '-' . str_pad($ctr,3,"0", STR_PAD_LEFT) . ".". pathinfo($a, PATHINFO_EXTENSION);
                                    if(is_file($scanD . "/" . $dir . "/" . $newname))
                                    {
                                        for($i=0;$i<1000;$i++)
                                        {
                                            $newname = str_replace(" ", "-", $dirCleaned) . '-' . str_pad($i,3,"0", STR_PAD_LEFT) . ".". pathinfo($a, PATHINFO_EXTENSION);
                                            if(!is_file($scanD . "/" . $dir . "/" . $newname))
                                            {
                                                $ctr=$i;
                                                $i=1000;
                                            }
                                        }

                                    }

                                    rename($scanD ."/".$dir . "/" .$oldFileName, $scanD ."/".$dir . "/" .$newname);
                                    array_push($processedOGFiles, $oldFileName);
                                    array_push($processedFiles, $oldFileName);
                                    array_push($processedFiles, $newname);
                                    consoleLog("ADDING: ".$newname);
                                }
                                $ctr++;
                            } else if (in_array($a,$prevOGScanned)) {
                                consoleLog("DELETE: " . $a);
                                unlink($scanD ."/".$dir . "/" .$a);
                            } else if (in_array($a,$prevScanned)) {
                                consoleLog("Previously Processed: " . $a);
                            }
                        }

                        $changedFiles = json_encode(array_merge($prevScanned,$processedFiles));
                        $fullScanFile = fopen($scanD . "/" . $dir. "/_scanned.json", "w") or die("Unable to open file!");
                        fwrite($fullScanFile, $changedFiles);
                        fclose($fullScanFile);

                        $originalFiles = json_encode(array_merge($prevOGScanned,$processedOGFiles));
                        $originalNamesFile = fopen($scanD . "/" . $dir. "/_originals.json", "w") or die("Unable to open file!");
                        fwrite($originalNamesFile, $originalFiles);
                        fclose($originalNamesFile);
                    }
                } else {
                    consoleLog("ERROR");
                }
            }
        }
    } else {
        consoleLog($scanD . " not found!");
    }
}

consoleLog("[COMPLETED]");